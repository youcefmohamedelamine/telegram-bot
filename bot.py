import json
import os
from datetime import datetime

class BotDashboardCLI:
    def __init__(self):
        self.orders = self.load_orders()

    def load_orders(self):
        """تحميل الطلبات من الملف"""
        if os.path.exists("orders.json"):
            with open("orders.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_orders(self):
        """حفظ الطلبات في الملف"""
        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(self.orders, f, indent=4, ensure_ascii=False)

    def show_stats(self):
        """عرض الإحصائيات"""
        total_orders = len(self.orders)
        completed_orders = sum(1 for o in self.orders.values() if o.get("status") == "completed")
        waiting_orders = sum(1 for o in self.orders.values() if o.get("status") == "waiting_id")
        total_revenue = sum(o.get("amount", 0) for o in self.orders.values())

        print("\n📊 الإحصائيات:")
        print(f"📦 إجمالي الطلبات: {total_orders}")
        print(f"✅ المكتملة: {completed_orders}")
        print(f"⏳ بانتظار ID: {waiting_orders}")
        print(f"💰 الإيرادات: {total_revenue} ⭐")

    def list_orders(self):
        """عرض كل الطلبات"""
        if not self.orders:
            print("🚫 لا توجد طلبات بعد")
            return
        print("\n📋 قائمة الطلبات:")
        for user_id, order in self.orders.items():
            time = order.get("time", "")
            if time:
                try:
                    time = datetime.fromisoformat(time).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            print(f"""
🆔 المستخدم: {user_id}
🎮 FF ID: {order.get('freefire_id', 'غير متوفر')}
💰 المبلغ: {order.get('amount', 0)} ⭐
📌 الحالة: {order.get('status', 'غير معروف')}
🕒 الوقت: {time}
""")

    def add_order(self):
        """إضافة طلب"""
        user_id = input("🆔 أدخل معرف المستخدم: ")
        ff_id = input("🎮 أدخل Free Fire ID: ")
        amount = int(input("💰 أدخل المبلغ (نجوم): "))

        self.orders[user_id] = {
            "freefire_id": ff_id,
            "amount": amount,
            "status": "waiting_id",
            "time": datetime.now().isoformat()
        }
        self.save_orders()
        print("✅ تم إضافة الطلب بنجاح!")

    def show_report(self):
        """تقرير شامل"""
        total_orders = len(self.orders)
        completed = sum(1 for o in self.orders.values() if o.get("status") == "completed")
        waiting = sum(1 for o in self.orders.values() if o.get("status") == "waiting_id")
        revenue = sum(o.get("amount", 0) for o in self.orders.values())

        print(f"""
📊 التقرير الشامل
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 إجمالي الطلبات: {total_orders}
✅ مكتملة: {completed}
⏳ بانتظار ID: {waiting}
❌ ملغاة: {total_orders - completed - waiting}
💰 الإيرادات: {revenue} ⭐
📊 متوسط الطلب: {revenue/total_orders if total_orders > 0 else 0:.2f}
📅 التاريخ: {datetime.now().strftime("%Y-%m-%d %H:%M")}
""")

    def run(self):
        """تشغيل القائمة النصية"""
        while True:
            print("""
━━━━━━━━━━━━━━━━━━━━━
🎮 لوحة تحكم البوت (CLI)
1️⃣ عرض الإحصائيات
2️⃣ قائمة الطلبات
3️⃣ إضافة طلب جديد
4️⃣ تقرير شامل
0️⃣ خروج
━━━━━━━━━━━━━━━━━━━━━
""")
            choice = input("اختر رقم: ").strip()
            if choice == "1":
                self.show_stats()
            elif choice == "2":
                self.list_orders()
            elif choice == "3":
                self.add_order()
            elif choice == "4":
                self.show_report()
            elif choice == "0":
                print("👋 تم الخروج.")
                break
            else:
                print("⚠️ خيار غير صحيح!")

if __name__ == "__main__":
    BotDashboardCLI().run()
