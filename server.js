const express = require('express');
const cors = require('cors');
const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;
const dbFile = path.join(__dirname, 'users.json');
const botToken = process.env.BOT_TOKEN || '7580086418:AAEE0shvKADPHNjaV-RyoBn0yO4IERyhUQQ';
const bot = new TelegramBot(botToken);
const webhookUrl = process.env.WEBHOOK_URL || 'https://nothing-store-backend.up.railway.app/bot';

// Middleware
app.use(cors());
app.use(express.json());

// تهيئة قاعدة البيانات
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

// نظام الرتب
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

// API: الحصول على إحصائيات المستخدم
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

// API: تحديث إحصائيات المستخدم
app.post('/api/user/:userId/update', async (req, res) => {
  try {
    const userId = req.params.userId;
    const { totalSpent, orderCount } = req.body;

    const db = await readDatabase();
    const rank = getRank(totalSpent);
    db[userId] = { totalSpent, orderCount, rank };
    await writeDatabase(db);

    res.json({ success: true, user: db[userId] });
  } catch (error) {
    console.error('خطأ في تحديث بيانات المستخدم:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// API: استقبال طلب الشراء
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
      provider_token: process.env.PAYMENT_PROVIDER_TOKEN || '', // أضف رمز مزود الدفع
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

// Webhook للبوت
app.post('/bot', (req, res) => {
  bot.processUpdate(req.body);
  res.sendStatus(200);
});

// معالجة أحداث البوت
bot.on('pre_checkout_query', async (query) => {
  try {
    await bot.answerPreCheckoutQuery(query.id, true);
  } catch (error) {
    console.error('خطأ في معالجة pre_checkout_query:', error);
  }
});

bot.on('successful_payment', async (msg) => {
  try {
    const { userId, category, amount } = JSON.parse(msg.successful_payment.invoice_payload);
    const db = await readDatabase();
    const userData = db[userId] || { totalSpent: 0, orderCount: 0 };
    userData.totalSpent = (userData.totalSpent || 0) + amount;
    userData.orderCount = (userData.orderCount || 0) + 1;
    userData.rank = getRank(userData.totalSpent);
    db[userId] = userData;
    await writeDatabase(db);

    await bot.sendMessage(userId, '🎉 تم الدفع بنجاح! شكرًا لشرائك لاشيء!');
  } catch (error) {
    console.error('خطأ في معالجة الدفع الناجح:', error);
    await bot.sendMessage(msg.from.id, '❌ حدث خطأ أثناء معالجة الدفع.');
  }
});

// إعداد Webhook
async function setupWebhook() {
  try {
    await bot.deleteWebhook();
    await bot.setWebhook(webhookUrl);
    console.log(`✅ Webhook تم تعيينه على: ${webhookUrl}`);
  } catch (error) {
    console.error('❌ خطأ في إعداد Webhook:', error);
  }
}

// تشغيل الخادم
async function startServer() {
  await initializeDatabase();
  await setupWebhook();
  app.listen(port, () => {
    console.log(`الخادم يعمل على http://localhost:${port}`);
  });
}

startServer();
