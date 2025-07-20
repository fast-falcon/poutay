from conf.settings import (
    QRC_FILE,          # مسیر فایل qrc اصلی
    QRC_FILE_FULL,     # مسیر فایل qrc کامل و ساخته شده (خروجی)
    COMPILED_QRC_PY,   # مسیر فایل پایتون ساخته شده از qrc
    PYSIDE6_RCC_PATH,  # مسیر ابزار pyside6-rcc برای کامپایل qrc
)


class SvgColorBuilder:
    def __init__(self, colors, output_svg_dirs):
        self.colors = colors
        self.output_svg_dirs = output_svg_dirs
        # مسیر فایل اصلی qrc
        self.qrc_path = Path(QRC_FILE)
        # دایرکتوری فایل qrc (برای محاسبه مسیرهای نسبی)
        self.qrc_dir = self.qrc_path.parent
        # دایرکتوری برای ذخیره svg های رنگی (اگر وجود نداشت ایجاد می‌شود)
        self.svg_colors_dir = Path(self.output_svg_dirs)
        self.svg_colors_dir.mkdir(parents=True, exist_ok=True)

        # مسیر فایل qrc کامل که ساخته می‌شود
        self.qrc_full_path = Path(QRC_FILE_FULL)
        # مسیر فایل پایتون خروجی qrc
        self.compiled_qrc_py = Path(COMPILED_QRC_PY)

    def build(self):
        # خواندن محتوای فایل qrc اصلی به صورت متن
        qrc_text = self.qrc_path.read_text(encoding="utf-8")
        # پارس کردن متن qrc به درخت xml
        tree = ET.ElementTree(ET.fromstring(qrc_text))
        root = tree.getroot()

        # ایجاد یک qresource جدید با prefix="auto" برای svg های رنگی ساخته شده
        auto_qresource = ET.Element("qresource", prefix="auto")
        # افزودن این qresource به انتهای ریشه فایل qrc
        root.append(auto_qresource)

        # پیمایش تمام qresource ها در فایل qrc
        for qresource in root.findall(".//qresource"):
            # از پردازش qresource جدید (auto) که خودمان ساختیم عبور کن
            if qresource is auto_qresource:
                continue

            # گرفتن لیست همه فایل‌ها در qresource جاری
            files = list(qresource.findall("file"))
            for file_elem in files:
                # گرفتن مسیر فایل به صورت متن و حذف فاصله اضافی
                file_path = file_elem.text.strip()

                # اگر فایل svg نیست، رد شو
                if not file_path.endswith(".svg"):
                    continue

                # مسیر کامل فایل svg اصلی
                abs_path = self.qrc_dir / file_path
                # خواندن متن svg
                svg_text = abs_path.read_text(encoding="utf-8")
                # پارس کردن svg با BeautifulSoup برای تغییر رنگ‌ها
                svg_soup = BeautifulSoup(svg_text, "xml")

                for color_name, color_value in self.colors.items():
                    # جستجوی همه تگ‌های <path> که ویژگی fill دارند و تغییر رنگ آنها
                    for path_tag in svg_soup.find_all("path"):
                        if path_tag.has_attr("fill"):
                            path_tag["fill"] = color_value

                    # نام فایل جدید برای svg رنگی
                    base_name = abs_path.stem
                    new_name = f"{base_name}_{color_name}.svg"

                    # مسیر کامل فایل svg جدید داخل فولدر SVG_COLORS_DIR
                    abs_new_path = self.svg_colors_dir / new_name
                    # ذخیره svg رنگی در مسیر مشخص شده
                    abs_new_path.write_text(str(svg_soup), encoding="utf-8")

                    # مسیر نسبی فایل جدید نسبت به دایرکتوری qrc (برای وارد کردن در فایل qrc)
                    relative_new_path = abs_new_path.relative_to(self.qrc_dir)
                    # ایجاد تگ file جدید برای افزودن به qresource auto
                    new_elem = ET.Element("file")
                    # تنظیم متن تگ file با مسیر نسبی و اصلاح جداکننده‌ها برای لینوکس و ویندوز
                    new_elem.text = str(relative_new_path).replace("\\", "/")

                    # افزودن تگ file جدید به qresource auto
                    auto_qresource.append(new_elem)

        # تبدیل ساختار xml به رشته متن (برای ذخیره)
        output = ET.tostring(root, encoding="unicode")
        # زیباسازی خروجی با minidom (برای indentation بهتر)
        dom = minidom.parseString(output)
        pretty = dom.toprettyxml(indent="  ", encoding=None)
        # حذف اولین خط xml declaration (<?xml version=...>)
        pretty_no_header = "\n".join(pretty.splitlines()[1:])
        # ذخیره متن نهایی در فایل QRC_FILE_FULL
        self.qrc_full_path.write_text(pretty_no_header, encoding="utf-8")

        print(f"✅ QRC_FILE_FULL updated: {self.qrc_full_path}")

        # اگر حالت DEBUG فعال است و فایل کامپایل شده قبلا ساخته شده
        print("[+] Compiling QRC → Python ...")
        # اجرای دستور کامپایل qrc به فایل پایتون
        subprocess.run(
            [PYSIDE6_RCC_PATH, str(self.qrc_full_path), "-o", str(self.compiled_qrc_py)],
            check=True,
        )
        print(f"✅ Compiled: {self.compiled_qrc_py}")
