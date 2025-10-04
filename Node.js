const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');

const app = express();
const port = 3000;
const dbFile = path.join(__dirname, 'users.json');

// Middleware
app.use(cors());
app.use(express.json());

// تهيئة قاعدة البيانات إذا لم تكن موجودة
async function initializeDatabase() {
  try {
    await fs.access(dbFile);
  } catch {
    await fs.writeFile(dbFile, JSON.stringify({}));
  }
}

// قراءة قاعدة البيانات
async function readDatabase() {
  const data = await fs.readFile(dbFile, 'utf-8');
  return JSON.parse(data);
}

// كتابة قاعدة البيانات
async function writeDatabase(data) {
  await fs.writeFile(dbFile, JSON.stringify(data, null, 2));
}

// الحصول على إحصائيات المستخدم
app.get('/api/user/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    const db = await readDatabase();
    const userData = db[userId] || { totalSpent: 0, orderCount: 0, rank: 'زائر جديد 🌱' };
    res.json(userData);
  } catch (error) {
    console.error('خطأ في جلب بيانات المستخدم:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// تحديث إحصائيات المستخدم (يستخدمه البوت)
app.post('/api/user/:userId/update', async (req, res) => {
  try {
    const userId = req.params.userId;
    const { totalSpent, orderCount } = req.body;

    const db = await readDatabase();
    const ranks = [
      { min: 500000, title: 'إمبراطور العدم 👑' },
      { min: 300000, title: 'ملك اللاشيء 💎' },
      { min: 200000, title: 'أمير الفراغ 🏆' },
      { min: 100000, title: 'نبيل العدم ⭐' },
      { min: 50000, title: 'فارس اللاشيء 🌟' },
      { min: 20000, title: 'تاجر العدم ✨' },
      { min: 10000, title: 'مبتدئ اللاشيء 🎯' },
      { min: 0, title: 'زائر جديد 🌱' }
    ];

    const rank = ranks.find(r => totalSpent >= r.min)?.title || 'زائر جديد 🌱';
    
    db[userId] = { totalSpent, orderCount, rank };
    await writeDatabase(db);
    
    res.json({ success: true, user: db[userId] });
  } catch (error) {
    console.error('خطأ في تحديث بيانات المستخدم:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// استقبال طلب الشراء من التطبيق
app.post('/api/buy', async (req, res) => {
  try {
    const { userId, category, amount } = req.body;
    if (!userId || !category || !amount) {
      return res.status(400).json({ error: 'بيانات غير كاملة' });
    }

    const db = await readDatabase();
    const userData = db[userId] || { totalSpent: 0, orderCount: 0 };

    // إرسال إشارة إلى البوت (يفترض أن البوت يستمع إلى هذا)
    // هنا يمكنك استخدام Telegram Bot API لإنشاء فاتورة
    // للتبسيط، نفترض أن البوت سيحدث البيانات لاحقًا
    res.json({ success: true, message: 'تم إرسال طلب الشراء إلى البوت' });
  } catch (error) {
    console.error('خطأ في معالجة الشراء:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// تشغيل الخادم
async function startServer() {
  await initializeDatabase();
  app.listen(port, () => {
    console.log(`الخادم يعمل على http://localhost:${port}`);
  });
}

startServer();
