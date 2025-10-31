#!/usr/bin/env python3
"""
اسکریپت ساده برای ساخت requirements.txt
تمام پکیج‌های نصب شده رو با pip freeze می‌گیره
"""

import subprocess
import sys
from pathlib import Path


def generate_requirements(output_file: str = "requirements.txt"):
    """ساخت فایل requirements.txt با pip freeze"""
    
    print("🚀 در حال دریافت لیست پکیج‌های نصب شده...")
    print("="*60)
    
    try:
        # اجرای pip freeze
        result = subprocess.run(
            ['pip', 'freeze'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # نوشتن در فایل
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        # نمایش لیست
        packages = result.stdout.strip().split('\n')
        print(f"\n📦 پکیج‌های پیدا شده:\n")
        for pkg in packages:
            if pkg.strip():
                print(f"   ✅ {pkg}")
        
        print("\n" + "="*60)
        print(f"✨ فایل {output_file} با موفقیت ساخته شد!")
        print("="*60)
        print(f"📊 تعداد کل پکیج‌ها: {len(packages)}")
        print(f"📁 مسیر فایل: {Path(output_file).absolute()}")
        print("\n💡 برای نصب این پکیج‌ها:")
        print(f"   pip install -r {output_file}")
        print("="*60)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در اجرای pip freeze: {e}")
        return False
        
    except FileNotFoundError:
        print("❌ pip پیدا نشد!")
        print("💡 مطمئن شوید که Python و pip به درستی نصب شده‌اند.")
        return False
        
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ساخت فایل requirements.txt از پکیج‌های نصب شده',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
مثال‌ها:
  python generate_requirements.py
  python generate_requirements.py -o requirements.txt
  python generate_requirements.py --output my_requirements.txt

این اسکریپت تمام پکیج‌های نصب شده در محیط فعلی Python را
با استفاده از 'pip freeze' استخراج می‌کند.
        """
    )
    
    parser.add_argument(
        '-o', '--output',
        default='requirements.txt',
        help='نام فایل خروجی (پیش‌فرض: requirements.txt)'
    )
    
    args = parser.parse_args()
    
    success = generate_requirements(args.output)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()