const express = require('express');
const cors = require('cors');
const TelegramBot = require('node-telegram-bot-api');
const { Pool } = require('pg'); // ✨ إضافة مكتبة PostgreSQL

const app = express();
const port = process.env.PORT || 3000;
// حذف: dbFile و fs و path

const botToken = process.env.BOT_TOKEN; // الاعتماد على متغير البيئة فقط
const bot = new TelegramBot(botToken);
const webhookUrl = process.env.WEBHOOK_URL; 
// تأكد أن BOT_TOKEN و WEBHOOK_URL مضافة كمتغيرات في Railway

// إنشاء تجمع اتصال (Pool) لاستخدامه في جميع استعلامات قاعدة البيانات
const pool = new Pool({
    connectionString: process.env.DATABASE_URL, // متغير يوفره Railway تلقائياً
    ssl: { rejectUnauthorized: false } // ضروري للاتصال السحابي الآمن
});

// Middleware
app.use(cors());
app.use(express.json());

// حذف: initializeDatabase، readDatabase، و writeDatabase (لم يعد الكود يحتاجها)

// نظام الرتب (كما هو)
const RANKS = [
  { min: 500000, title: 'إمبراطور العدم 👑' },
  { min: 300000, title: 'ملك اللاشيء 💎' },
  { min: 200000, title: 'أمير الفراغ 🏆' },
  { min: 100000, title: 'نبيل العدم ⭐' },
  { min: 50000, title: 'فارس اللاشيء 🌟' },
  { min: 20000, title: 'تاجر العدم ✨' },
  { min: 10000, title: 'مبتدئ اللاشيء 🎯' },
  { min: 0, title: 'زائر جديد 🌱' }
];

function getRank(totalSpent) {
  for (let rank of RANKS) {
    if (totalSpent >= rank.min) {
      return rank.title;
    }
  }
  return RANKS[RANKS.length - 1].title;
}

// ✨ دالة جلب/إنشاء المستخدم (للتعامل مع PostgreSQL)
async function findOrCreateUser(userId) {
    // 1. محاولة جلب المستخدم
    let result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
    
    if (result.rows.length > 0) {
        return result.rows[0]; 
    }

    // 2. إذا لم يكن موجوداً، قم بإنشائه (Insert)
    const initialRank = getRank(0);
    const insertResult = await pool.query(
        'INSERT INTO users (id, total_spent, order_count, rank) VALUES ($1, $2, $3, $4) RETURNING *',
        [userId, 0, 0, initialRank]
    );
    return insertResult.rows[0]; 
}


// API: الحصول على إحصائيات المستخدم (محدث)
app.get('/api/user/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    // جلب البيانات من DB عبر الدالة الجديدة
    const userData = await findOrCreateUser(userId); 
    res.json(userData);
  } catch (error) {
    console.error('خطأ في جلب بيانات المستخدم:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// API: تحديث إحصائيات المستخدم (محدث)
app.post('/api/user/:userId/update', async (req, res) => {
  try {
    const userId = req.params.userId;
    const { totalSpent, orderCount } = req.body;

    const rank = getRank(totalSpent);
    
    // تحديث البيانات في PostgreSQL
    await pool.query(
        'UPDATE users SET total_spent = $2, order_count = $3, rank = $4 WHERE id = $1',
        [userId, totalSpent, orderCount, rank]
    );

    res.json({ success: true, user: { totalSpent, orderCount, rank } });
  } catch (error) {
    console.error('خطأ في تحديث بيانات المستخدم:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// API: استقبال طلب الشراء (كما هو)
app.post('/api/buy', async (req, res) => {
  try {
    const { userId, category, amount } = req.body;
    if (!userId || !category || !amount) {
      return res.status(400).json({ error: 'بيانات غير كاملة' });
    }

    // إرسال فاتورة إلى المستخدم
    await bot.sendInvoice(userId, {
      title: `شراء لاشيء ${category}`,
      description: `شراء لاشيء بحجم ${category} بقيمة ${amount} ⭐`,
      payload: JSON.stringify({ userId, category, amount }),
      provider_token: process.env.PAYMENT_PROVIDER_TOKEN || '', 
      currency: 'XTR',
      prices: [{ label: `لاشيء ${category}`, amount: amount * 100 }],
      start_parameter: 'buy'
    });

    res.json({ success: true, message: 'تم إرسال فاتورة الشراء' });
  } catch (error) {
    console.error('خطأ في معالجة الشراء:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// Webhook للبوت (كما هو)
app.post('/bot', (req, res) => {
  bot.processUpdate(req.body);
  res.sendStatus(200);
});

// معالجة أحداث البوت (pre_checkout_query كما هو)
bot.on('pre_checkout_query', async (query) => {
  try {
    await bot.answerPreCheckoutQuery(query.id, true);
  } catch (error) {
    console.error('خطأ في معالجة pre_checkout_query:', error);
  }
});

// معالجة الدفع الناجح (محدث)
bot.on('successful_payment', async (msg) => {
  try {
    const { userId, category, amount } = JSON.parse(msg.successful_payment.invoice_payload);
    
    // 1. جلب البيانات الحالية من DB
    const user = await findOrCreateUser(userId); 
    
    // 2. حساب القيم الجديدة
    const newTotalSpent = user.total_spent + amount;
    const newOrderCount = user.order_count + 1;
    const newRank = getRank(newTotalSpent);

    // 3. تحديث البيانات في PostgreSQL
    await pool.query(
        'UPDATE users SET total_spent = $2, order_count = $3, rank = $4 WHERE id = $1',
        [userId, newTotalSpent, newOrderCount, newRank]
    );
    
    await bot.sendMessage(userId, '🎉 تم الدفع بنجاح! شكرًا لشرائك لاشيء!');
  } catch (error) {
    console.error('خطأ في معالجة الدفع الناجح:', error);
    await bot.sendMessage(msg.from.id, '❌ حدث خطأ أثناء معالجة الدفع.');
  }
});

// إعداد Webhook (كما هو)
async function setupWebhook() {
  try {
    await bot.deleteWebhook();
    await bot.setWebhook(webhookUrl);
    console.log(`✅ Webhook تم تعيينه على: ${webhookUrl}`);
  } catch (error) {
    console.error('❌ خطأ في إعداد Webhook:', error);
  }
}

// تشغيل الخادم (محدث)
async function startServer() {
  try {
        // اختبار الاتصال بـ PostgreSQL قبل البدء
        await pool.query('SELECT NOW()'); 
        console.log('✅ تم الاتصال بقاعدة بيانات PostgreSQL بنجاح!');
        
        await setupWebhook();
        app.listen(port, () => {
            console.log(`الخادم يعمل على منفذ: ${port}`);
        });
    } catch (e) {
        console.error('❌ فشل تشغيل الخادم والاتصال بقاعدة البيانات:', e);
        process.exit(1);
    }
}

startServer();
