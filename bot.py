import React, { useState } from 'react';
import { ShoppingCart, Code, Zap, Package, AlertCircle, Laugh } from 'lucide-react';

const CleanTemplatesStore = () => {
  const [cart, setCart] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [currentLang, setCurrentLang] = useState(null);

  const STAR_PRICE = 999;
  
  const templates = {
    python: {
      name: "main.py",
      emoji: "🐍",
      desc: "Python النظيف",
      joke: "الملف الوحيد الذي لن يرميه الـ garbage collector! 🗑️"
    },
    javascript: {
      name: "index.js",
      emoji: "💛",
      desc: "JavaScript الصافي",
      joke: "بدون undefined، بدون null، بس أنت ومشاكلك! 😅"
    },
    java: {
      name: "Main.java",
      emoji: "☕",
      desc: "Java المركز",
      joke: "3 مليار جهاز يشغلون Java... وأنت بعدك ما بلشت! ⏰"
    },
    cpp: {
      name: "main.cpp",
      emoji: "⚡",
      desc: "C++ السريع",
      joke: "سريع لدرجة إنه بيخلص قبل ما تفهم الكود! 🏃‍♂️"
    },
    csharp: {
      name: "Program.cs",
      emoji: "🔷",
      desc: "C# الاحترافي",
      joke: "Microsoft وافقت عليه شخصياً! (مش حقيقي بس يبان كويس) 🎭"
    },
    php: {
      name: "index.php",
      emoji: "🐘",
      desc: "PHP الجديد",
      joke: "نعم، الناس لسا بتستعمل PHP في 2025! 🦕"
    },
    html: {
      name: "index.html",
      emoji: "🌐",
      desc: "HTML النقي",
      joke: "بدون Bootstrap! نعم، هتكتب كل حاجة بإيدك يا بطل! 💪"
    },
    css: {
      name: "style.css",
      emoji: "🎨",
      desc: "CSS الفاضي",
      joke: "مش هنحط !important في كل سطر، وعد! 🤞"
    },
    go: {
      name: "main.go",
      emoji: "🔵",
      desc: "Go المنطلق",
      joke: "Google عملته عشان محدش يفهم C++ تاني! 🤯"
    },
    rust: {
      name: "main.rs",
      emoji: "🦀",
      desc: "Rust الآمن",
      joke: "الـ Compiler هيزعلك قبل ما البرنامج يشتغل! 😤"
    }
  };

  const funnyReasons = [
    "🎪 لأن حياتك محتاجة شوية فضاء... في الكود على الأقل!",
    "🍕 أخف من بيتزا دومينوز (بس أغلى شوية)",
    "🎭 مكتوب بحب... ومسح بحب أكتر!",
    "🌟 الملفات دي فاضية لدرجة إنها فلسفية!",
    "🎪 كل المبرمجين المشهورين بدأوا من صفحة بيضا (أو كذبوا)",
    "🎨 أحسن من لوحة بيكاسو... على الأقل دي بتشتغل!",
    "🚀 ناسا بتستخدمها (في أحلامنا)",
    "💎 نظيفة لدرجة إن Marie Kondo هتفرح!",
    "🎯 الكود الوحيد اللي مش فيه bugs... لسه!",
    "🏆 فازت بجائزة 'أفضل ملف فاضي' 3 سنين متتالية!"
  ];

  const addToCart = (lang) => {
    if (!cart.includes(lang)) {
      setCart([...cart, lang]);
    }
  };

  const buyBundle = () => {
    setCart(Object.keys(templates));
    setShowModal(true);
  };

  const getTotalPrice = () => {
    return cart.length === 10 ? STAR_PRICE * 10 : cart.length * STAR_PRICE;
  };

  const showDetails = (lang) => {
    setCurrentLang(lang);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      {/* Header */}
      <header className="bg-black bg-opacity-50 backdrop-blur-md p-6 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Code className="w-10 h-10 text-yellow-400" />
            <div>
              <h1 className="text-3xl font-bold">متجر القوالب "النظيفة" 😂</h1>
              <p className="text-sm text-gray-300">لأن الكود الفاضي أحسن من الكود الغلط!</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-purple-600 px-4 py-2 rounded-full flex items-center gap-2">
              <ShoppingCart className="w-5 h-5" />
              <span className="font-bold">{cart.length}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-12">
        <div className="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-3xl p-8 text-center text-black mb-12">
          <h2 className="text-4xl font-bold mb-4">🎉 العرض الخرافي!</h2>
          <p className="text-2xl mb-6">10 ملفات فاضية تماماً بـ ⭐{STAR_PRICE * 10} نجمة فقط!</p>
          <button 
            onClick={buyBundle}
            className="bg-black text-white px-8 py-4 rounded-full text-xl font-bold hover:bg-gray-800 transition-all transform hover:scale-105"
          >
            <Package className="inline mr-2" />
            اشتري الباقة الكاملة (وفر 0%)
          </button>
          <p className="text-sm mt-3">* التوفير وهمي، بس الملفات حقيقية! 😉</p>
        </div>

        {/* Funny Reasons */}
        <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl p-8 mb-12">
          <h3 className="text-3xl font-bold mb-6 text-center flex items-center justify-center gap-3">
            <Laugh className="w-8 h-8 text-yellow-400" />
            ليه القوالب النظيفة؟
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {funnyReasons.map((reason, idx) => (
              <div key={idx} className="bg-black bg-opacity-30 p-4 rounded-xl hover:bg-opacity-50 transition-all">
                <p className="text-lg">{reason}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(templates).map(([lang, template]) => (
            <div 
              key={lang}
              className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl p-6 hover:bg-opacity-20 transition-all transform hover:scale-105 cursor-pointer"
              onClick={() => showDetails(lang)}
            >
              <div className="text-6xl mb-4 text-center">{template.emoji}</div>
              <h3 className="text-2xl font-bold mb-2 text-center">{template.desc}</h3>
              <p className="text-yellow-300 text-center mb-4 min-h-[60px]">{template.joke}</p>
              <div className="flex gap-2">
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    addToCart(lang);
                  }}
                  className={`flex-1 py-3 rounded-xl font-bold transition-all ${
                    cart.includes(lang) 
                      ? 'bg-green-600' 
                      : 'bg-purple-600 hover:bg-purple-700'
                  }`}
                >
                  {cart.includes(lang) ? '✓ في السلة' : `⭐${STAR_PRICE}`}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Cart Summary */}
      {cart.length > 0 && (
        <div className="fixed bottom-6 right-6 bg-purple-600 rounded-2xl p-6 shadow-2xl max-w-sm">
          <h3 className="text-xl font-bold mb-3">🛒 سلة المشتريات</h3>
          <div className="space-y-2 mb-4">
            {cart.map(lang => (
              <div key={lang} className="flex items-center gap-2 bg-black bg-opacity-30 p-2 rounded-lg">
                <span className="text-2xl">{templates[lang].emoji}</span>
                <span className="flex-1">{templates[lang].name}</span>
                <button 
                  onClick={() => setCart(cart.filter(l => l !== lang))}
                  className="text-red-400 hover:text-red-300"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <div className="border-t border-white border-opacity-30 pt-3 mb-3">
            <div className="flex justify-between items-center text-xl font-bold">
              <span>المجموع:</span>
              <span className="text-yellow-400">⭐{getTotalPrice()}</span>
            </div>
          </div>
          <button 
            onClick={() => setShowModal(true)}
            className="w-full bg-yellow-400 text-black py-3 rounded-xl font-bold hover:bg-yellow-300 transition-all"
          >
            <Zap className="inline mr-2" />
            اشتري الآن!
          </button>
        </div>
      )}

      {/* Details Modal */}
      {currentLang && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4" onClick={() => setCurrentLang(null)}>
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full" onClick={e => e.stopPropagation()}>
            <div className="text-center mb-6">
              <div className="text-8xl mb-4">{templates[currentLang].emoji}</div>
              <h2 className="text-3xl font-bold mb-2">{templates[currentLang].desc}</h2>
              <p className="text-yellow-300 text-xl">{templates[currentLang].joke}</p>
            </div>
            <div className="bg-black rounded-xl p-6 mb-6">
              <code className="text-green-400 text-sm whitespace-pre-wrap">
{`// ${templates[currentLang].name}
// ملف نظيف 100%
// جاهز للاستخدام!

function main() {
    // اكتب كودك هنا يا فنان! 🎨
}

main();`}
              </code>
            </div>
            <div className="flex gap-4">
              <button 
                onClick={() => {
                  addToCart(currentLang);
                  setCurrentLang(null);
                }}
                className="flex-1 bg-purple-600 hover:bg-purple-700 py-3 rounded-xl font-bold transition-all"
              >
                أضف للسلة ⭐{STAR_PRICE}
              </button>
              <button 
                onClick={() => setCurrentLang(null)}
                className="px-6 bg-gray-700 hover:bg-gray-600 py-3 rounded-xl font-bold transition-all"
              >
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Purchase Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl p-8 max-w-md w-full text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-3xl font-bold mb-4">مبروك!</h2>
            <p className="text-xl mb-6">
              اشتريت {cart.length} ملف فاضي بنجاح! 
              <br />
              (كان ممكن تعملهم بنفسك بس خلينا نتفائل 😂)
            </p>
            <div className="bg-white bg-opacity-20 rounded-xl p-4 mb-6">
              <p className="text-2xl font-bold mb-2">المجموع المدفوع:</p>
              <p className="text-4xl font-bold text-yellow-300">⭐{getTotalPrice()}</p>
            </div>
            <button 
              onClick={() => {
                setShowModal(false);
                setCart([]);
              }}
              className="w-full bg-white text-black py-3 rounded-xl font-bold hover:bg-gray-200 transition-all"
            >
              رجوع للصفحة الرئيسية
            </button>
            <p className="text-xs mt-4 text-gray-200">
              * هذا تطبيق تجريبي، لا يوجد دفع حقيقي (للأسف) 💸
            </p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-black bg-opacity-50 backdrop-blur-md mt-20 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-xl mb-4">
            💡 <strong>نصيحة الخبراء:</strong> الكود الفاضي أسهل في الصيانة من الكود المليان bugs!
          </p>
          <p className="text-sm text-gray-400">
            © 2025 متجر القوالب النظيفة | كل الحقوق محفوظة (حتى لو الملفات فاضية) 😄
          </p>
        </div>
      </footer>
    </div>
  );
};

export default CleanTemplatesStore;
