import os
import fitz  # PyMuPDF
import easyocr
from pillow import Image as PILImage

from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.clock import Clock

# تصميم الواجهة الاحترافية المحدثة بلغة KV باللون الداكن والنيون الأزرق
KV = '''
MDScreen:
    md_bg_color: 0.05, 0.08, 0.12, 1  # خلفية داكنة مريحة جداً للعين

    # القائمة الجانبية (Navigation Drawer) لرفع الملف
    MDNavigationDrawer:
        id: nav_drawer
        radius: (0, 16, 16, 0)
        md_bg_color: 0.08, 0.12, 0.18, 1
        
        MDBoxLayout:
            orientation: 'vertical'
            padding: "16dp"
            spacing: "20dp"
            
            MDLabel:
                text: "إعدادات التطبيق"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: 0.12, 0.65, 0.95, 1
                halign: "center"
                size_hint_y: None
                height: "40dp"
                
            MDRaisedButton:
                text: "📁 تحميل ملف PDF"
                md_bg_color: 0.12, 0.53, 0.90, 1
                pos_hint: {"center_x": .5}
                size_hint_x: 0.9
                on_release: 
                    nav_drawer.set_state("close")
                    app.open_file_manager()
            
            Widget: # فراغ ممتد لأسفل القائمة

    # الواجهة الرئيسية للتطبيق
    MDBoxLayout:
        orientation: 'vertical'
        padding: ["16dp", "10dp", "16dp", "10dp"]
        spacing: "15dp"

        # المنطقة العلوية: تحتوي فقط على زر القائمة الجانبية بأعلى اليمين لتوفير المساحة
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "40dp"
            
            Widget: # لدفع الأيقونة إلى جهة اليمين تماماً
            
            MDIconButton:
                icon: "menu"
                icon_size: "28sp"
                theme_icon_color: "Custom"
                icon_color: 0.12, 0.65, 0.95, 1
                on_release: nav_drawer.set_state("open")

        # بار البحث اليدوي الفوري على شكل كبسولة نيون عائمة
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "60dp"
            padding: ["10dp", "0dp", "10dp", "0dp"]
            
            MDTextField:
                id: search_bar
                hint_text: "...ابحث يدوياً هنا (فوري)"
                mode: "round"
                fill_color_normal: 0.08, 0.12, 0.18, 1
                line_color_focus: 0.12, 0.65, 0.95, 1
                hint_text_color_normal: 0.4, 0.5, 0.6, 1
                text_color_normal: 1, 1, 1, 1
                text_color_focus: 1, 1, 1, 1
                on_text: app.on_manual_search(self.text)

        # شاشة عرض الصفحات والنتائج بنظام زجاجي رمادي داكن متباين
        MDCard:
            orientation: "vertical"
            padding: "20dp"
            size_hint: (1, 0.55)
            pos_hint: {"center_x": 0.5}
            elevation: 0
            md_bg_color: 0.08, 0.12, 0.18, 0.8  # زجاجي شبه شفاف
            radius: [20, 20, 20, 20]
            line_color: 0.15, 0.22, 0.32, 1
            line_width: 1.2

            MDScrollView:
                MDLabel:
                    id: result_label
                    text: "مرحباً بك، محمد! قم برفع ملف PDF أولاً، ثم ابدأ البحث الذكي."
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.75, 0.8, 1
                    font_style: "Body1"
                    size_hint_y: None
                    height: self.texture_size[1]

        # أزرار التحكم السفلي والتنقل الموحد بين التكرارات (السابق والتالي)
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: (1, None)
            height: "50dp"
            spacing: "15dp"

            MDRaisedButton:
                id: btn_prev
                text: "⬅️ السابق"
                disabled: True
                md_bg_color: 0.15, 0.22, 0.32, 1
                disabled_color: 0.08, 0.12, 0.18, 1
                on_release: app.navigate_results(-1)
                size_hint_x: 0.5
                radius: [12, 12, 12, 12]

            MDRaisedButton:
                id: btn_next
                text: "التالي ➡️"
                disabled: True
                md_bg_color: 0.15, 0.22, 0.32, 1
                disabled_color: 0.08, 0.12, 0.18, 1
                on_release: app.navigate_results(1)
                size_hint_x: 0.5
                radius: [12, 12, 12, 12]

        # زر الكاميرا الرئيسي الدائري المحاط بوميض
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: "90dp"
            pos_hint: {"center_x": 0.5}
            
            MDFloatingActionButton:
                icon: "camera-iris"
                icon_size: "32sp"
                md_bg_color: 0.12, 0.65, 0.95, 1
                pos_hint: {"center_x": .5}
                on_release: app.open_camera_ocr()

        # التوثيق وحفظ الحقوق أسفل اليسار بشكل انسيابي خافت
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "25dp"
            
            MDLabel:
                text: "تصميم: محمد حسان حبيب"
                halign: "left"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.3, 0.4, 0.5, 1
'''

class SmartSearchApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.pdf_document = None
        self.pdf_text_by_page = []
        self.search_results = []
        self.current_result_index = -1
        
        # تهيئة مدير الملفات ومحرك الـ OCR للغة الإنجليزية
        self.file_manager = MDFileManager(
            exit_manager=self.close_file_manager,
            select_path=self.select_pdf_path,
            preview=False
        )
        self.ocr_reader = easyocr.Reader(['en'])
        
        return Builder.load_string(KV)

    # --- إدارة ملف الـ PDF ---
    def open_file_manager(self):
        path = os.getenv('EXTERNAL_STORAGE', '/')
        self.file_manager.show(path)

    def close_file_manager(self, *args):
        self.file_manager.close()

    def select_pdf_path(self, path):
        self.close_file_manager()
        if path.endswith('.pdf'):
            try:
                self.pdf_document = fitz.open(path)
                self.pdf_text_by_page = [page.get_text().lower() for page in self.pdf_document]
                
                self.root.ids.result_label.text = f"🟢 تم تحميل الملف بنجاح:\n\n{os.path.basename(path)}\n\nيمكنك الآن استخدام البحث الفوري أو تصوير سؤالك."
                self.root.ids.result_label.text_color = (0.12, 0.65, 0.95, 1)
            except Exception as e:
                self.show_dialog("خطأ", "فشل في فتح ملف الـ PDF المختار.")
        else:
            self.show_dialog("تنبيه", "الرجاء اختيار ملف بصيغة PDF فقط.")

    # --- البحث اليدوي الفوري المباشر الحرف بحرف ---
    def on_manual_search(self, text):
        if not self.pdf_document:
            return
        
        query = text.strip().lower()
        if not query:
            self.root.ids.result_label.text = "اكتب أي كلمة أو حرف للبحث الفوري..."
            self.reset_navigation()
            return
        
        # فلترة الصفحات فورياً تبعاً للمكتوب
        self.search_results = [idx for idx, page_text in enumerate(self.pdf_text_by_page) if query in page_text]
        
        if self.search_results:
            self.current_result_index = 0
            self.update_search_ui()
        else:
            self.root.ids.result_label.text = f"❌ لم يتم العثور على أي نتائج تطابق: '{text}'"
            self.reset_navigation()

    # --- معالجة صورة الكاميرا بالذكاء الاصطناعي (OCR) ---
    def open_camera_ocr(self):
        if not self.pdf_document:
            self.show_dialog("تنبيه", "برجاء رفع ملف الـ PDF من القائمة أولاً قبل استخدام الكاميرا.")
            return
        
        image_path = "captured_question.png"
        
        if os.path.exists(image_path):
            self.root.ids.result_label.text = "⏳ جاري قراءة ومسح السؤال بالذكاء الاصطناعي..."
            Clock.schedule_once(lambda dt: self.process_ocr(image_path), 0.1)
        else:
            self.show_dialog("الكاميرا", "يرجى تأكيد التقاط الصورة وإعطاء الصلاحيات للهاتف.")

    def process_ocr(self, image_path):
        try:
            results = self.ocr_reader.readtext(image_path, detail=0)
            extracted_text = " ".join(results).strip().lower()
            
            if extracted_text:
                self.root.ids.search_bar.text = extracted_text  # يكتب النص المستخرج في كبسولة البحث تلقائياً
                self.on_manual_search(extracted_text)
            else:
                self.root.ids.result_label.text = "لم نتمكن من قراءة النص، يرجى تحسين الإضاءة وزاوية التصوير."
        except Exception as e:
            self.root.ids.result_label.text = "حدث خطأ غير متوقع أثناء المعالجة الذكية للصورة."

    # --- تحديث شاشة العرض والتنقل التلقائي للموقع ---
    def update_search_ui(self):
        total_results = len(self.search_results)
        page_num = self.search_results[self.current_result_index] + 1
        
        self.root.ids.result_label.text = (
            f"🔍 تم العثور على النص المبحوث عنه!\n\n"
            f"📍 رقم الصفحة في الـ PDF: [ {page_num} ]\n\n"
            f"🔄 التكرار: نتيجة {self.current_result_index + 1} من إجمالي {total_results} نتائج."
        )
        
        if total_results > 1:
            self.root.ids.btn_prev.disabled = False
            self.root.ids.btn_next.disabled = False
        else:
            self.reset_navigation()

    def navigate_results(self, direction):
        if not self.search_results:
            return
        self.current_result_index = (self.current_result_index + direction) % len(self.search_results)
        self.update_search_ui()

    def reset_navigation(self):
        self.root.ids.btn_prev.disabled = True
        self.root.ids.btn_next.disabled = True

    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[MDFlatButton(text="حسناً", text_color=(0.12, 0.65, 0.95, 1), on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

if __name__ == '__main__':
    SmartSearchApp().run()