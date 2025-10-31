#!/usr/bin/env python3
"""
اسکریپت تمیزکاری پروژه پایتون
حذف تمام کامنت‌ها، docstringها و فایل‌های غیرضروری
"""

import os
import sys
import shutil
from pathlib import Path

class PythonProjectCleaner:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.files_processed = 0
        self.files_cleaned = 0
        
        self.ignore_patterns = {
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'env',
            '.pytest_cache',
            '.mypy_cache',
            'node_modules',
            '.idea',
            '.vscode',
            'dist',
            'build',
            '*.egg-info'
        }
        
        self.files_to_delete = {
            '.pyc',
            '.pyo',
            '.pyd',
            '.DS_Store',
            'Thumbs.db',
            '.coverage',
            '.pytest_cache'
        }

    def should_ignore(self, path: Path) -> bool:
        for pattern in self.ignore_patterns:
            if pattern in str(path):
                return True
        return False

    def remove_all_comments_and_docstrings(self, code: str) -> str:
        lines = code.split('\n')
        cleaned_lines = []
        in_multiline_string = False
        string_delimiter = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            if in_multiline_string:
                if string_delimiter in line:
                    in_multiline_string = False
                    string_delimiter = None
                i += 1
                continue
            
            if stripped.startswith('"""') or stripped.startswith("'''"):
                delimiter = '"""' if stripped.startswith('"""') else "'''"
                
                if stripped.count(delimiter) >= 2:
                    i += 1
                    continue
                else:
                    in_multiline_string = True
                    string_delimiter = delimiter
                    i += 1
                    continue
            
            new_line = []
            in_string = False
            current_quote = None
            j = 0
            
            while j < len(line):
                if j + 2 < len(line) and line[j:j+3] in ['"""', "'''"]:
                    quote = line[j:j+3]
                    rest_of_line = line[j+3:]
                    
                    if quote in rest_of_line:
                        end_pos = rest_of_line.index(quote)
                        j = j + 3 + end_pos + 3
                        continue
                    else:
                        in_multiline_string = True
                        string_delimiter = quote
                        break
                
                char = line[j]
                
                if char in ['"', "'"] and (j == 0 or line[j-1] != '\\'):
                    if not in_string:
                        in_string = True
                        current_quote = char
                    elif char == current_quote:
                        in_string = False
                        current_quote = None
                    new_line.append(char)
                    j += 1
                    continue
                
                if char == '#' and not in_string:
                    break
                
                new_line.append(char)
                j += 1
            
            result = ''.join(new_line).rstrip()
            if result.strip():
                cleaned_lines.append(result)
            elif len(cleaned_lines) > 0 and cleaned_lines[-1].strip():
                cleaned_lines.append('')
            
            i += 1
        
        return '\n'.join(cleaned_lines)

    def remove_excessive_empty_lines(self, code: str) -> str:
        lines = code.split('\n')
        cleaned = []
        empty_count = 0
        
        for line in lines:
            if not line.strip():
                empty_count += 1
                if empty_count <= 1:
                    cleaned.append(line)
            else:
                empty_count = 0
                cleaned.append(line)
        
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        
        return '\n'.join(cleaned)

    def clean_python_file(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            cleaned_code = self.remove_all_comments_and_docstrings(original_code)
            cleaned_code = self.remove_excessive_empty_lines(cleaned_code)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_code)
            
            self.files_cleaned += 1
            return True
            
        except Exception as e:
            print(f"❌ خطا در پردازش {file_path}: {e}")
            return False

    def delete_unnecessary_files(self):
        deleted_count = 0
        
        for root, dirs, files in os.walk(self.root_path):
            dirs_to_remove = []
            for dir_name in dirs:
                if dir_name in self.ignore_patterns:
                    dir_path = Path(root) / dir_name
                    try:
                        shutil.rmtree(dir_path)
                        print(f"🗑️  حذف پوشه: {dir_path}")
                        deleted_count += 1
                        dirs_to_remove.append(dir_name)
                    except Exception as e:
                        print(f"❌ خطا در حذف {dir_path}: {e}")
            
            for dir_name in dirs_to_remove:
                dirs.remove(dir_name)
            
            for file_name in files:
                file_path = Path(root) / file_name
                if any(file_name.endswith(ext) for ext in self.files_to_delete):
                    try:
                        file_path.unlink()
                        print(f"🗑️  حذف فایل: {file_path}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"❌ خطا در حذف {file_path}: {e}")
        
        print(f"\n✅ {deleted_count} فایل/پوشه غیرضروری حذف شد")

    def process_project(self):
        print("🚀 شروع تمیزکاری پروژه...")
        print(f"📁 مسیر پروژه: {self.root_path.absolute()}\n")
        
        print("🗑️  مرحله 1: حذف فایل‌ها و پوشه‌های غیرضروری...")
        self.delete_unnecessary_files()
        
        print("\n🧹 مرحله 2: حذف کامنت‌ها و docstringها از فایل‌های پایتون...")
        
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if not self.should_ignore(file_path):
                        python_files.append(file_path)
        
        print(f"📊 تعداد فایل‌های پایتون: {len(python_files)}\n")
        
        for file_path in python_files:
            self.files_processed += 1
            print(f"🔧 در حال پردازش: {file_path.relative_to(self.root_path)}")
            self.clean_python_file(file_path)
        
        print("\n" + "="*60)
        print("✨ تمیزکاری پروژه با موفقیت انجام شد!")
        print("="*60)
        print(f"📊 آمار:")
        print(f"   • فایل‌های پردازش شده: {self.files_processed}")
        print(f"   • فایل‌های تمیز شده: {self.files_cleaned}")
        print("="*60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='تمیزکاری کامل پروژه پایتون - حذف تمام کامنت‌ها و docstringها'
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='مسیر پروژه (پیش‌فرض: پوشه جاری)'
    )
    
    args = parser.parse_args()
    
    project_path = Path(args.path)
    if not project_path.exists():
        print(f"❌ خطا: مسیر '{project_path}' وجود ندارد!")
        sys.exit(1)
    
    if not project_path.is_dir():
        print(f"❌ خطا: '{project_path}' یک پوشه نیست!")
        sys.exit(1)
    
    print(f"⚠️  توجه: این اسکریپت تمام کامنت‌ها و docstringها را حذف می‌کند!")
    print(f"📁 مسیر پروژه: {project_path.absolute()}")
    response = input("\n❓ آیا می‌خواهید ادامه دهید؟ (y/n): ")
    
    if response.lower() != 'y':
        print("❌ عملیات لغو شد.")
        sys.exit(0)
    
    cleaner = PythonProjectCleaner(args.path)
    cleaner.process_project()


if __name__ == "__main__":
    main()