import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime
from threading import Thread

# ============= واجهة إدارة البوت =============
class BotDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 لوحة تحكم بوت فري فاير")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f2f5")
        
        # تحميل البيانات
        self.orders = self.load_orders()
        
        # إنشاء الواجهة
        self.create_header()
        self.create_stats_section()
        self.create_orders_table()
        self.create_control_panel()
        
    def load_orders(self):
        """تحميل الطلبات من الملف"""
        try:
            if os.path.exists("orders.json"):
                with open("orders.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_orders(self):
        """حفظ الطلبات في الملف"""
        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(self.orders, f, indent=4, ensure_ascii=False)
    
    def create_header(self):
        """إنشاء الترويسة"""
        header_frame = tk.Frame(self.root, bg="#6c5ce7", height=100)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🎮 لوحة تحكم بوت فري فاير",
            font=("Arial", 28, "bold"),
            bg="#6c5ce7",
            fg="white"
        )
        title_label.pack(pady=25)
    
    def create_stats_section(self):
        """إنشاء قسم الإحصائيات"""
        stats_frame = tk.Frame(self.root, bg="#f0f2f5")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # إحصائيات
        total_orders = len(self.orders)
        completed_orders = sum(1 for o in self.orders.values() if o.get("status") == "completed")
        waiting_orders = sum(1 for o in self.orders.values() if o.get("status") == "waiting_id")
        total_revenue = sum(o.get("amount", 0) for o in self.orders.values())
        
        stats = [
            ("📦 إجمالي الطلبات", total_orders, "#6c5ce7"),
            ("✅ الطلبات المكتملة", completed_orders, "#00b894"),
            ("⏳ بانتظار ID", waiting_orders, "#fdcb6e"),
            ("💰 الإيرادات", f"{total_revenue} ⭐", "#0984e3")
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg=color, relief=tk.RAISED, borderwidth=2)
            card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
            
            tk.Label(
                card,
                text=label,
                font=("Arial", 12),
                bg=color,
                fg="white"
            ).pack(pady=(15, 5))
            
            tk.Label(
                card,
                text=str(value),
                font=("Arial", 24, "bold"),
                bg=color,
                fg="white"
            ).pack(pady=(0, 15))
    
    def create_orders_table(self):
        """إنشاء جدول الطلبات"""
        table_frame = tk.Frame(self.root, bg="white", relief=tk.RAISED, borderwidth=2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # عنوان الجدول
        header = tk.Frame(table_frame, bg="#341f97", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📋 قائمة الطلبات",
            font=("Arial", 18, "bold"),
            bg="#341f97",
            fg="white"
        ).pack(pady=10)
        
        # إنشاء Treeview
        tree_frame = tk.Frame(table_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ("user_id", "freefire_id", "amount", "status", "time")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=15
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # تعريف الأعمدة
        self.tree.heading("user_id", text="معرف المستخدم")
        self.tree.heading("freefire_id", text="Free Fire ID")
        self.tree.heading("amount", text="المبلغ")
        self.tree.heading("status", text="الحالة")
        self.tree.heading("time", text="الوقت")
        
        self.tree.column("user_id", width=150, anchor="center")
        self.tree.column("freefire_id", width=150, anchor="center")
        self.tree.column("amount", width=100, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        self.tree.column("time", width=200, anchor="center")
        
        # تنسيق الجدول
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=35,
            fieldbackground="white",
            font=("Arial", 11)
        )
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#dfe6e9")
        style.map("Treeview", background=[("selected", "#6c5ce7")])
        
        # إضافة البيانات
        self.refresh_table()
        
        # ربط حدث النقر المزدوج
        self.tree.bind("<Double-1>", self.on_row_double_click)
        
        # وضع العناصر
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def refresh_table(self):
        """تحديث جدول الطلبات"""
        # حذف البيانات القديمة
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # إضافة البيانات الجديدة
        status_text = {
            "waiting_id": "⏳ بانتظار ID",
            "completed": "✅ مكتمل",
            "processing": "🔄 قيد المعالجة"
        }
        
        for user_id, order in self.orders.items():
            freefire_id = order.get("freefire_id", "لم يُرسل")
            amount = f"{order.get('amount', 0)} ⭐"
            status = status_text.get(order.get("status", ""), "غير معروف")
            time = order.get("time", "")
            if time:
                try:
                    time = datetime.fromisoformat(time).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            self.tree.insert("", "end", values=(user_id, freefire_id, amount, status, time))
    
    def create_control_panel(self):
        """إنشاء لوحة التحكم"""
        control_frame = tk.Frame(self.root, bg="#f0f2f5")
        control_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        buttons = [
            ("🔄 تحديث", self.refresh_data, "#0984e3"),
            ("➕ إضافة طلب", self.add_order, "#00b894"),
            ("📊 تقرير مفصل", self.show_report, "#fdcb6e"),
            ("⚙️ الإعدادات", self.show_settings, "#6c5ce7")
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                control_frame,
                text=text,
                command=command,
                font=("Arial", 12, "bold"),
                bg=color,
                fg="white",
                relief=tk.RAISED,
                borderwidth=3,
                padx=20,
                pady=10,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, expand=True, padx=5)
            
            # تأثيرات الماوس
            btn.bind("<Enter>", lambda e, b=btn: b.configure(relief=tk.SUNKEN))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(relief=tk.RAISED))
    
    def on_row_double_click(self, event):
        """عند النقر المزدوج على صف"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        values = self.tree.item(selected_item[0])["values"]
        user_id = values[0]
        
        # نافذة تفاصيل الطلب
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"تفاصيل الطلب - {user_id}")
        detail_window.geometry("500x400")
        detail_window.configure(bg="white")
        
        order = self.orders.get(str(user_id), {})
        
        details = f"""
╔═══════════════════════════════════╗
║        📋 تفاصيل الطلب        ║
╚═══════════════════════════════════╝

🆔 معرف المستخدم: {user_id}

🎮 Free Fire ID: {order.get('freefire_id', 'لم يُرسل')}

💰 المبلغ: {order.get('amount', 0)} نجمة ⭐

📌 الحالة: {order.get('status', 'غير معروف')}

🕒 الوقت: {order.get('time', 'غير محدد')}

        """
        
        text_widget = scrolledtext.ScrolledText(
            detail_window,
            font=("Arial", 12),
            wrap=tk.WORD,
            bg="#f8f9fa",
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text_widget.insert("1.0", details)
        text_widget.configure(state="disabled")
        
        # زر إغلاق
        tk.Button(
            detail_window,
            text="إغلاق",
            command=detail_window.destroy,
            font=("Arial", 12, "bold"),
            bg="#d63031",
            fg="white",
            padx=30,
            pady=10
        ).pack(pady=(0, 20))
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.orders = self.load_orders()
        self.refresh_table()
        messagebox.showinfo("✅ نجح", "تم تحديث البيانات بنجاح!")
    
    def add_order(self):
        """إضافة طلب جديد"""
        messagebox.showinfo("ℹ️ معلومة", "هذه الميزة قيد التطوير")
    
    def show_report(self):
        """عرض تقرير مفصل"""
        report_window = tk.Toplevel(self.root)
        report_window.title("📊 التقرير المفصل")
        report_window.geometry("600x500")
        report_window.configure(bg="white")
        
        total_orders = len(self.orders)
        completed = sum(1 for o in self.orders.values() if o.get("status") == "completed")
        waiting = sum(1 for o in self.orders.values() if o.get("status") == "waiting_id")
        revenue = sum(o.get("amount", 0) for o in self.orders.values())
        
        report = f"""
╔═══════════════════════════════════╗
║        📊 التقرير الشامل        ║
╚═══════════════════════════════════╝

📈 إحصائيات عامة:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 إجمالي الطلبات: {total_orders}
✅ الطلبات المكتملة: {completed}
⏳ بانتظار ID: {waiting}
❌ ملغاة: {total_orders - completed - waiting}

💰 الإيرادات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐ إجمالي النجوم: {revenue}
📊 متوسط الطلب: {revenue/total_orders if total_orders > 0 else 0:.2f}

📅 التاريخ: {datetime.now().strftime("%Y-%m-%d %H:%M")}

        """
        
        text_widget = scrolledtext.ScrolledText(
            report_window,
            font=("Arial", 12),
            wrap=tk.WORD,
            bg="#f8f9fa",
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text_widget.insert("1.0", report)
        text_widget.configure(state="disabled")
    
    def show_settings(self):
        """عرض الإعدادات"""
        messagebox.showinfo("⚙️ الإعدادات", "صفحة الإعدادات قيد التطوير")


# ============= تشغيل التطبيق =============
if __name__ == "__main__":
    root = tk.Tk()
    app = BotDashboard(root)
    root.mainloop()
