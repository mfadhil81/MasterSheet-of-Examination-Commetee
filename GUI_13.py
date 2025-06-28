import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import pickle
import export_to_excel_Universal2025
from qr_code_handler import scan_qr_with_camera
from pyzbar.pyzbar import decode
from PIL import Image
import cv2


# دالة لفتح الكاميرا والتحقق من QR Code
def scan_qr_with_camera(license_id):
    cap = cv2.VideoCapture(0)
    print("قم بتوجيه QR Code أمام الكاميرا للتحقق من الترخيص...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("لم يتم العثور على كاميرا.")
            break

        decoded_objs = decode(frame)
        for obj in decoded_objs:
            qr_data = obj.data.decode("utf-8")
            if qr_data == license_id:
                print("تم التحقق من الترخيص بنجاح!")
                cap.release()
                cv2.destroyAllWindows()
                return True

        cv2.imshow("QR Code Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("فشل التحقق من الترخيص.")
    return False

class MasterSheetApp :
    def __init__(self, root) :
        self.root = root
        self.root.title("ماستر شيت لدرجات الطلبة")
        self.root.geometry("800x600")

        # متغيرات لتخزين البيانات من ملفات الإكسل
        self.students_df = None
        self.materials_df = None
        self.committee_df = None

        # تحميل البيانات المحفوظة من المرة السابقة
        self.load_saved_data()

        # الإطار الجانبي للخيارات
        self.sidebar = tk.Frame(root, width=200, bg='lightgrey')
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self.sidebar, text="خيارات", bg='lightgrey', font=("Arial", 14, "bold")).pack(pady=10)

        # زر لإنشاء ماستر شيت
        tk.Button(self.sidebar, text="إنشاء ماستر شيت للنظام السنوي", command=self.export_master_sheet).pack(pady=5, padx=10,
                                                                                               fill=tk.X)
        # زر لإيجاد إحصائيات النجاح
        tk.Button(self.sidebar, text="إحصائيات النجاح", command=self.show_statistics).pack(pady=5, padx=10, fill=tk.X)
        # زر لتصميم QR للحماية
        #tk.Button(self.sidebar, text="إنشاء QR للحماية", command=self.create_qr_code).pack(pady=5, padx=10, fill=tk.X)

        # قسم المدخلات
        self.create_input_section()

        # قسم عرض الملفات
        self.create_file_display_section()

        # حفظ المدخلات عند إغلاق البرنامج
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_input_section(self) :
        """إنشاء قسم المدخلات للبيانات العامة."""
        frame = tk.Frame(self.root)
        frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        inputs = [
            ("اسم الجامعة:", "university_name"),
            ("اسم الكلية:", "college_name"),
            ("اسم القسم/الفرع:", "department_name"),
            ("عدد الطلبة:", "num_students"),
            ("المرحلة:", "stage"),
            ("رئيس القسم/الفرع:", "head_of_department"),
            ("العام الدراسي:", "academic_year"),
        ]

        self.entries = {}
        for i, (label, key) in enumerate(inputs) :
            tk.Label(frame, text=label).grid(row=i, column=0, sticky='e', padx=5)
            entry = tk.Entry(frame)
            entry.grid(row=i, column=1, sticky='w')
            entry.insert(0, self.saved_data.get(key, ""))
            self.entries[key] = entry

    def create_file_display_section(self) :
        """إنشاء قسم عرض الملفات بعد تحميلها."""
        frame = tk.Frame(self.root)
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # أزرار تحميل الملفات
        self.load_students_button = tk.Button(frame, text="تحميل ملف أسماء الطلاب",
                                              command=lambda : self.load_excel_file('students'))
        self.load_students_button.grid(row=0, column=0, pady=5)

        self.load_materials_button = tk.Button(frame, text="تحميل ملف أسماء المواد",
                                               command=lambda : self.load_excel_file('materials'))
        self.load_materials_button.grid(row=0, column=1, pady=5)

        self.load_committee_button = tk.Button(frame, text="تحميل ملف أسماء اللجنة الامتحانية",
                                               command=lambda : self.load_excel_file('committee'))
        self.load_committee_button.grid(row=0, column=2, pady=5)

        # شجرة عرض الملفات
        self.tree = ttk.Treeview(frame)
        self.tree.grid(row=1, column=0, columnspan=3, sticky='nsew')

        # تخطيط الشبكة
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

    def load_excel_file(self, file_type) :
        """تحميل ملف إكسل وعرضه."""
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if not file_path :
            return

        try :
            df = pd.read_excel(file_path)
            setattr(self, f"{file_type}_df", df)
            self.display_data_in_tree(df)
            messagebox.showinfo("نجاح", f"تم تحميل بيانات {file_type} بنجاح!")
        except Exception as e :
            messagebox.showerror("خطأ", f"فشل تحميل الملف: {str(e)}")

    def display_data_in_tree(self, df) :
        """عرض البيانات في شجرة الجدول."""
        self.tree.delete(*self.tree.get_children())
        self.tree["column"] = list(df.columns)
        self.tree["show"] = "headings"

        for col in df.columns :
            self.tree.heading(col, text=col)

        for _, row in df.iterrows() :
            self.tree.insert("", "end", values=list(row))

    def show_statistics(self) :
        """عرض إحصائيات النجاح."""
        if self.students_df is None or self.materials_df is None :
            messagebox.showerror("خطأ", "يرجى تحميل بيانات الطلاب والمواد أولاً!")
            return

        # حساب نسبة النجاح
        success_rate = self.calculate_success_rate()
        messagebox.showinfo("إحصائيات النجاح", f"نسبة النجاح: {success_rate:.2f}%")

    def calculate_success_rate(self) :
        """حساب نسبة النجاح بناءً على الدرجات."""
        pass  # تعتمد على منطق محدد لحساب نسبة النجاح

    def export_master_sheet(self) :
        """إنشاء ماستر شيت باستخدام exportExcel1."""
        if self.students_df is None or self.materials_df is None or self.committee_df is None :
            messagebox.showerror("خطأ", "يرجى تحميل جميع الملفات الثلاثة!")
            return

        try :
            num_students = int(self.entries["num_students"].get())
            export_to_excel_Universal2025.export_to_excel1(
                self.students_df, self.materials_df, self.committee_df,
                self.entries["university_name"].get(), self.entries["college_name"].get(),
                self.entries["department_name"].get(), num_students,
                self.entries["stage"].get(), self.entries["head_of_department"].get(),
                self.entries["academic_year"].get()
            )
            messagebox.showinfo("نجاح", "تم إنشاء الماستر شيت بنجاح!")
        except ValueError :
            messagebox.showerror("خطأ", "يرجى إدخال عدد صحيح لعدد الطلبة.")

    def load_saved_data(self) :
        """تحميل البيانات المحفوظة سابقًا."""
        try :
            with open("saved_data.pkl", "rb") as f :
                self.saved_data = pickle.load(f)
        except FileNotFoundError :
            self.saved_data = {}

    def save_data(self) :
        """حفظ البيانات المدخلة."""
        for key, entry in self.entries.items() :
            self.saved_data[key] = entry.get()

        with open("saved_data.pkl", "wb") as f :
            pickle.dump(self.saved_data, f)

    def on_closing(self) :
        """حفظ البيانات عند الإغلاق."""
        self.save_data()
        self.root.destroy()

# دالة لقراءة محتوى QR Code من الملف "license_qr.png"
def get_license_id_from_qr():
    try:
        img = Image.open("license_qr.png")
        decoded_objs = decode(img)
        if decoded_objs:
            return decoded_objs[0].data.decode("utf-8")
    except Exception as e:
        print(f"خطأ في قراءة QR Code: {str(e)}")
    return None

# بدء التطبيق مع التحقق من QR Code
def start_app():
    license_id = get_license_id_from_qr()  # قراءة معرف الترخيص من QR Code المحفوظ
    if license_id and scan_qr_with_camera(license_id):
        root = tk.Tk()
        app = MasterSheetApp(root)
        root.mainloop()
    else:
        print("لم يتم التحقق من الترخيص. تأكد من صحة QR Code.")

if __name__ == "__main__":
    start_app()
