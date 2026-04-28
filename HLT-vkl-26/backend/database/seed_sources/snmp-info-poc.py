#!/usr/bin/env python3
import subprocess
import sys
from typing import List, Tuple

# ==========================================================
# SNMP Community String List
# Anh có thể thêm/bớt community string tại đây.
# Ví dụ: COMMUNITY_STRINGS = ["public", "private", "cisco"]
# ==========================================================
COMMUNITY_STRINGS = [
    "cisco",
    "public",
    "private",
]

# SNMP OIDs cần lấy
OID_SYSTEM_INFO = ".1.3.6.1.2.1.1.1"
OID_INTERFACE_NAME = ".1.3.6.1.2.1.2.2.1.2"
OID_IP_ADDRESS = ".1.3.6.1.2.1.4.20.1.1"
OID_ALIAS = ".1.3.6.1.2.1.31.1.1.1.18"

# Timeout cho mỗi lệnh snmpwalk, tính bằng giây
COMMAND_TIMEOUT = 8


def run_snmpwalk(target: str, community: str, oid: str) -> Tuple[bool, List[str], str]:
    """
    Chạy snmpwalk an toàn bằng subprocess.

    Return:
        success: True nếu lệnh chạy thành công và có dữ liệu stdout
        lines: danh sách dòng kết quả
        error: thông báo lỗi nếu có
    """
    cmd = [
        "snmpwalk",
        "-v", "2c",
        "-c", community,
        "-Oqv",
        target,
        oid,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, [], "Timeout khi truy vấn SNMP"
    except FileNotFoundError:
        return False, [], "Không tìm thấy lệnh snmpwalk. Cần cài net-snmp/snmpwalk trước"
    except Exception as exc:
        return False, [], f"Lỗi khi chạy snmpwalk: {exc}"

    stdout_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    stderr_text = result.stderr.strip()

    if result.returncode != 0:
        return False, stdout_lines, stderr_text or f"snmpwalk trả về mã lỗi {result.returncode}"

    if not stdout_lines:
        return False, [], stderr_text or "Không có dữ liệu trả về"

    return True, stdout_lines, ""


def collect_snmp_data(target: str, community: str) -> dict:
    """
    Thu thập dữ liệu SNMP với một community string.
    """
    sys_ok, sys_info_raw, sys_err = run_snmpwalk(target, community, OID_SYSTEM_INFO)
    names_ok, names, names_err = run_snmpwalk(target, community, OID_INTERFACE_NAME)
    ips_ok, ips, ips_err = run_snmpwalk(target, community, OID_IP_ADDRESS)
    aliases_ok, aliases, aliases_err = run_snmpwalk(target, community, OID_ALIAS)

    has_data = any([
        sys_ok and bool(sys_info_raw),
        names_ok and bool(names),
        ips_ok and bool(ips),
        aliases_ok and bool(aliases),
    ])

    errors = []
    for label, ok, err in [
        ("System Info", sys_ok, sys_err),
        ("Interface Name", names_ok, names_err),
        ("IP Address", ips_ok, ips_err),
        ("Alias", aliases_ok, aliases_err),
    ]:
        if not ok and err:
            errors.append(f"{label}: {err}")

    return {
        "community": community,
        "has_data": has_data,
        "system_info": sys_info_raw[0] if sys_info_raw else "N/A",
        "names": names,
        "ips": ips,
        "aliases": aliases,
        "errors": errors,
    }


def print_result(target: str, result: dict) -> None:
    """
    In kết quả theo từng community string.
    """
    community = result["community"]

    print("\n" + "=" * 100)
    print(f"TARGET: {target}")
    print(f"COMMUNITY STRING: {community}")
    print("=" * 100)

    if not result["has_data"]:
        print(f"[KHÔNG CÓ KẾT QUẢ] Community string '{community}' không trả về dữ liệu.")
        if result["errors"]:
            print("Chi tiết:")
            for err in result["errors"]:
                print(f"- {err}")
        print("=" * 100)
        return

    print(f"[CÓ KẾT QUẢ] Community string '{community}' trả về dữ liệu SNMP.")
    print(f"System: {result['system_info']}")
    print("-" * 100)
    print(f"{'Interface':<35} | {'IP Address':<20} | {'Ghi chú Alias':<35}")
    print("-" * 100)

    names = result["names"]
    ips = result["ips"]
    aliases = result["aliases"]
    max_len = max(len(names), len(ips), len(aliases))

    if max_len == 0:
        print("Không có dữ liệu bảng interface/ip/alias, chỉ thu được thông tin system hoặc dữ liệu SNMP khác.")
    else:
        for i in range(max_len):
            name = names[i] if i < len(names) else "N/A"
            ip = ips[i] if i < len(ips) else "N/A"
            alias = aliases[i] if i < len(aliases) else ""
            print(f"{name:<35} | {ip:<20} | {alias:<35}")

    if result["errors"]:
        print("-" * 100)
        print("Một số OID không trả về dữ liệu:")
        for err in result["errors"]:
            print(f"- {err}")

    print("=" * 100)


def print_usage() -> None:
    print("Lỗi: Thiếu tham số IP.", file=sys.stderr)
    print("Cách dùng: python3 table2.py <ip>", file=sys.stderr)
    print("Ví dụ: python3 table2.py 192.168.1.1", file=sys.stderr)


def main() -> int:
    if len(sys.argv) != 2:
        print_usage()
        return 2

    target = sys.argv[1].strip()
    if not target:
        print_usage()
        return 2

    print("=" * 100)
    print("SNMP COMMUNITY STRING CHECK")
    print("=" * 100)
    print(f"Target: {target}")
    print(f"Số community string sẽ kiểm tra: {len(COMMUNITY_STRINGS)}")

    any_success = False

    for community in COMMUNITY_STRINGS:
        result = collect_snmp_data(target, community)
        print_result(target, result)
        if result["has_data"]:
            any_success = True

    print("\n" + "=" * 100)
    print("KẾT LUẬN")
    print("=" * 100)

    if any_success:
        print("TRUE - Có ít nhất một community string trả về dữ liệu SNMP.")
        return 0

    print("FALSE - Không có community string nào trả về dữ liệu SNMP.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
