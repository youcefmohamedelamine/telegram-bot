import React, { useState } from 'react';
import { Download, Code, Zap, CheckCircle, Star, Package, Info, Shield, X } from 'lucide-react';

const STAR_PRICE = 999;

const FILES = {
  python: {
    name: "main.py",
    content: `# Python Clean Template
# Zero bloat. Pure simplicity.
# Start your project the right way.

def main():
    pass

if __name__ == "__main__":
    main()`,
    emoji: "🐍",
    desc: "Clean Python Template",
    color: "from-blue-500 to-blue-600"
  },
  javascript: {
    name: "index.js",
    content: `// JavaScript Clean Template
// No frameworks. No dependencies. Just code.
// Perfect blank canvas for your project.

function main() {
    // Your code here
}

main();`,
    emoji: "💛",
    desc: "Clean JavaScript Template",
    color: "from-yellow-500 to-yellow-600"
  },
  java: {
    name: "Main.java",
    content: `// Java Clean Template
// Enterprise-ready blank structure
// Professional starting point

public class Main {
    public static void main(String[] args) {
        // Your code here
    }
}`,
    emoji: "☕",
    desc: "Clean Java Template",
    color: "from-orange-500 to-red-600"
  },
  cpp: {
    name: "main.cpp",
    content: `// C++ Clean Template
// Optimized structure. Zero overhead.
// Performance-first approach.

#include <iostream>
using namespace std;

int main() {
    // Your code here
    return 0;
}`,
    emoji: "⚡",
    desc: "Clean C++ Template",
    color: "from-purple-500 to-purple-600"
  },
  csharp: {
    name: "Program.cs",
    content: `// C# Clean Template
// .NET ready structure
// Professional blank slate

using System;

class Program
{
    static void Main(string[] args)
    {
        // Your code here
    }
}`,
    emoji: "🔷",
    desc: "Clean C# Template",
    color: "from-indigo-500 to-indigo-600"
  },
  php: {
    name: "index.php",
    content: `<?php
// PHP Clean Template
// Web-ready blank structure
// No bloat. Just potential.

function main() {
    // Your code here
}

main();
?>`,
    emoji: "🐘",
    desc: "Clean PHP Template",
    color: "from-violet-500 to-violet-600"
  },
  html: {
    name: "index.html",
    content: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clean HTML Template</title>
    <!-- Pure HTML. No frameworks. Full control. -->
</head>
<body>
    <!-- Your content here -->
</body>
</html>`,
    emoji: "🌐",
    desc: "Clean HTML Template",
    color: "from-red-500 to-pink-600"
  },
  css: {
    name: "style.css",
    content: `/* CSS Clean Template */
/* Zero bloat. Pure styling potential. */
/* Build your design from scratch. */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Your styles here */`,
    emoji: "🎨",
    desc: "Clean CSS Template",
    color: "from-pink-500 to-rose-600"
  },
  go: {
    name: "main.go",
    content: `// Go Clean Template
// Minimal structure. Maximum efficiency.
// Google's simplicity philosophy.

package main

import "fmt"

func main() {
    // Your code here
    fmt.Println("Ready to code!")
}`,
    emoji: "🔵",
    desc: "Clean Go Template",
    color: "from-cyan-500 to-cyan-600"
  },
  rust: {
    name: "main.rs",
    content: `// Rust Clean Template
// Memory-safe blank slate
// Zero-cost abstraction ready

fn main() {
    // Your code here
    println!("Ready to build!");
}`,
    emoji: "🦀",
    desc: "Clean Rust Template",
    color: "from-amber-500 to-orange-600"
  }
};

export default function CleanTemplatesApp() {
  const [currentView, setCurrentView] = useState('home');
  const [selectedFile, setSelectedFile] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [purchaseType, setPurchaseType] = useState(null);

  const handlePurchase = (type, fileKey = null) => {
    setPurchaseType(type);
    setSelectedFile(fileKey);
    setShowModal(true);
  };

  const processPayment = () => {
    // دوال الدفع الأصلية - لا تعديل عليها
    const payload = purchaseType === 'bundle' 
      ? `all_${Date.now()}` 
      : `file_${selectedFile}_${Date.now()}`;
    
    const price = purchaseType === 'bundle' ? STAR_PRICE * 10 : STAR_PRICE;
    
    console.log('Payment Processing:', {
      payload,
      price,
      currency: 'XTR',
      type: purchaseType
    });

    // محاكاة نجاح الدفع
    setTimeout(() => {
      handleSuccessfulPayment(payload, price);
    }, 1500);
  };

  const handleSuccessfulPayment = (payload, stars) => {
    // دالة الدفع الناجح الأصلية
    if (payload.includes('all_')) {
      downloadBundle();
      savePurchase('bundle.zip', stars);
    } else if (payload.includes('file_')) {
      const lang = payload.split('_')[1];
      downloadFile(lang);
      savePurchase(FILES[lang].name, stars);
    }
    
    setShowModal(false);
    alert('✅ تم الدفع بنجاح! جاري تحميل الملفات...');
  };

  const savePurchase = (fileName, stars) => {
    // حفظ عملية الشراء - الدالة الأصلية
    const purchase = {
      user_id: Date.now(),
      file_name: fileName,
      stars_paid: stars,
      purchase_date: new Date().toISOString()
    };
    console.log('Purchase saved:', purchase);
  };

  const downloadFile = (lang) => {
    const file = FILES[lang];
    const blob = new Blob([file.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadBundle = () => {
    // تحميل كل الملفات كـ ZIP (محاكاة)
    Object.values(FILES).forEach((file, index) => {
      setTimeout(() => downloadFile(Object.keys(FILES)[index]), index * 200);
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Code className="w-10 h-10 text-purple-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">Clean Code Templates</h1>
                <p className="text-sm text-gray-400">Zero Bloat. Pure Simplicity.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentView('home')}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition"
              >
                الرئيسية
              </button>
              <button
                onClick={() => setCurrentView('templates')}
                className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition"
              >
                القوالب
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-12">
        {currentView === 'home' && (
          <div className="space-y-12">
            {/* Hero Section */}
            <div className="text-center space-y-6 py-12">
              <div className="inline-block animate-bounce">
                <Zap className="w-20 h-20 text-yellow-400 mx-auto" />
              </div>
              <h2 className="text-5xl font-bold text-white">
                قوالب برمجية نظيفة
              </h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                ابدأ مشروعك بالطريقة الصحيحة. بدون تعقيدات، بدون أكواد زائدة، فقط الأساسيات
              </p>
              
              <div className="flex flex-wrap justify-center gap-4 pt-6">
                <div className="flex items-center gap-2 bg-green-500/20 px-6 py-3 rounded-lg border border-green-500/30">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-white">بنية احترافية</span>
                </div>
                <div className="flex items-center gap-2 bg-blue-500/20 px-6 py-3 rounded-lg border border-blue-500/30">
                  <Zap className="w-5 h-5 text-blue-400" />
                  <span className="text-white">بداية سريعة</span>
                </div>
                <div className="flex items-center gap-2 bg-purple-500/20 px-6 py-3 rounded-lg border border-purple-500/30">
                  <Shield className="w-5 h-5 text-purple-400" />
                  <span className="text-white">تحكم كامل</span>
                </div>
              </div>
            </div>

            {/* Bundle Offer */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur-xl opacity-50"></div>
              <div className="relative bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-8 text-center">
                <Package className="w-16 h-16 text-white mx-auto mb-4" />
                <h3 className="text-3xl font-bold text-white mb-2">الباقة الكاملة</h3>
                <p className="text-white/90 mb-4">احصل على جميع القوالب العشرة</p>
                <div className="flex items-center justify-center gap-2 mb-6">
                  <Star className="w-8 h-8 text-yellow-300 fill-yellow-300" />
                  <span className="text-5xl font-bold text-white">{STAR_PRICE * 10}</span>
                </div>
                <button
                  onClick={() => handlePurchase('bundle')}
                  className="bg-white text-purple-600 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition transform hover:scale-105"
                >
                  شراء الباقة الكاملة
                </button>
              </div>
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6">
                <div className="bg-red-500/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                  <X className="w-6 h-6 text-red-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">بدون أكواد زائدة</h3>
                <p className="text-gray-400">100% نظيف، لا توجد أمثلة تحتاج حذفها</p>
              </div>
              
              <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6">
                <div className="bg-green-500/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-green-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">ابدأ فوراً</h3>
                <p className="text-gray-400">لا تضيع وقت في تنظيف الكود</p>
              </div>
              
              <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6">
                <div className="bg-blue-500/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                  <Code className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">بنية احترافية</h3>
                <p className="text-gray-400">معايير صناعية وأفضل الممارسات</p>
              </div>
            </div>

            {/* Why Clean Section */}
            <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-lg border border-white/10 rounded-2xl p-8">
              <div className="flex items-start gap-4">
                <Info className="w-8 h-8 text-blue-400 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-2xl font-bold text-white mb-4">لماذا القوالب النظيفة أفضل؟</h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-lg font-semibold text-red-400 mb-2">❌ القوالب التقليدية:</h4>
                      <ul className="space-y-2 text-gray-300">
                        <li>• مليئة بأمثلة ستحذفها</li>
                        <li>• محملة بميزات غير مستخدمة</li>
                        <li>• تضيع الوقت في التنظيف</li>
                        <li>• مربكة للمبتدئين</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-green-400 mb-2">✅ قوالبنا النظيفة:</h4>
                      <ul className="space-y-2 text-gray-300">
                        <li>• 100% فارغة ونظيفة</li>
                        <li>• بنية احترافية فقط</li>
                        <li>• ابدأ البرمجة فوراً</li>
                        <li>• كودك، قواعدك</li>
                      </ul>
                    </div>
                  </div>
                  <p className="text-gray-300 mt-6 italic">
                    💡 "أفضل كود هو الكود الذي تكتبه بنفسك!"
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentView === 'templates' && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white text-center mb-8">
              اختر القالب المناسب لك
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(FILES).map(([key, file]) => (
                <div
                  key={key}
                  className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition group"
                >
                  <div className={`bg-gradient-to-br ${file.color} w-16 h-16 rounded-xl flex items-center justify-center text-3xl mb-4 group-hover:scale-110 transition`}>
                    {file.emoji}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{file.desc}</h3>
                  <p className="text-gray-400 text-sm mb-4">{file.name}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                      <span className="text-white font-bold">{STAR_PRICE}</span>
                    </div>
                    <button
                      onClick={() => handlePurchase('single', key)}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      شراء
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Payment Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-white/20 rounded-2xl p-8 max-w-md w-full">
            <h3 className="text-2xl font-bold text-white mb-4">تأكيد الدفع</h3>
            <div className="space-y-4 mb-6">
              <div className="flex justify-between text-gray-300">
                <span>العنصر:</span>
                <span className="font-bold text-white">
                  {purchaseType === 'bundle' ? 'الباقة الكاملة' : FILES[selectedFile]?.desc}
                </span>
              </div>
              <div className="flex justify-between text-gray-300">
                <span>السعر:</span>
                <div className="flex items-center gap-1">
                  <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                  <span className="font-bold text-white text-xl">
                    {purchaseType === 'bundle' ? STAR_PRICE * 10 : STAR_PRICE}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={processPayment}
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-xl font-bold hover:opacity-90 transition"
              >
                تأكيد الدفع
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="px-6 bg-white/10 text-white py-3 rounded-xl hover:bg-white/20 transition"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-black/30 backdrop-blur-lg border-t border-white/10 mt-20">
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p className="text-gray-400">
            🎯 Clean Code Templates - "Less is more" - Start clean, build big!
          </p>
        </div>
      </footer>
    </div>
  );
}
