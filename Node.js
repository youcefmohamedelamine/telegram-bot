const express = require('express');
const cors = require('cors');
const TelegramBot = require('node-telegram-bot-api');
// حذف استدعاء fs و path
const mongoose = require('mongoose'); // استدعاء Mongoose

const app = express();
const port = process.env.PORT || 3000;
// حذف dbFile
const botToken = process.env.BOT_TOKEN; // الاعتماد كلياً على متغير البيئة
const webhookUrl = process.env.WEBHOOK_URL;
const bot = new TelegramBot(botToken);

// Middleware
app.use(cors());
app.use(express.json());

// 1. تعريف نموذج البيانات (Schema)
const userSchema = new mongoose.Schema({
    _id: { type: String, required: true }, // استخدام User ID كـ _id للتحديد السهل
    totalSpent: { type: Number, default: 0 },
    orderCount: { type: Number, default: 0 },
    rank: { type: String, default: 'زائر جديد 🌱' }
});
const User = mongoose.model('User', userSchema);

// حذف initializeDatabase، readDatabase، و writeDatabase

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

// دالة جلب/إنشاء المستخدم
async function findOrCreateUser(userId) {
    let userData = await User.findById(userId);
    if (!userData) {
        // إنشاء مستخدم جديد إذا لم يكن موجوداً
        userData = await User.create({ 
            _id: userId,
            totalSpent: 0,
            orderCount: 0,
            rank: 'زائر جديد 🌱'
        });
    }
    return userData;
}


// API: الحصول على إحصائيات المستخدم (محدث)
app.get('/api/user/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    const userData = await findOrCreateUser(userId); // جلب البيانات من DB
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

    // تحديث البيانات في DB
    const updatedUser = await User.findByIdAndUpdate(userId, { 
        totalSpent, 
        orderCount, 
        rank 
    }, { new: true, upsert: true });

    res.json({ success: true, user: updatedUser });
  } catch (error) {
    console.error('خطأ في تحديث بيانات المستخدم:', error);
    res.status(500).json({ error: 'خطأ في السيرفر' });
  }
});

// API: استقبال طلب الشراء (لم يتغير المنطق، لكن يعتمد على DB لاحقاً)
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

// Webhook والبوت (لم يتغير)
app.post('/bot', (req, res) => {
  bot.processUpdate(req.body);
  res.sendStatus(200);
});

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

    // تحديث البيانات في قاعدة البيانات (محدث)
    const user = await findOrCreateUser(userId);
    user.totalSpent = (user.totalSpent || 0) + amount;
    user.orderCount = (user.orderCount || 0) + 1;
    user.rank = getRank(user.totalSpent);
    await user.save(); // حفظ التغييرات في DB

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

// 2. دالة الاتصال بقاعدة البيانات والتشغيل (محدث)
async function startServer() {
  try {
        // الاتصال بقاعدة البيانات
        const dbUrl = process.env.MONGO_URL; // أو DATABASE_URL لـ PostgreSQL
        if (!dbUrl) {
            console.error('❌ متغير MONGO_URL غير موجود. تأكد من إضافته في Railway!');
            process.exit(1);
        }
        await mongoose.connect(dbUrl);
        console.log('✅ تم الاتصال بقاعدة البيانات بنجاح!');
        
        // إعداد البوت والتشغيل
        await setupWebhook();
        app.listen(port, () => {
            console.log(`الخادم يعمل على منفذ: ${port}`);
        });
    } catch (e) {
        console.error('❌ فشل تشغيل الخادم:', e);
    }
}

startServer();
