import React, { useState } from 'react';
import { Download, Code, Package, Sparkles, Check, X, Menu, ChevronRight } from 'lucide-react';

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
    color: "from-blue-500 to-yellow-500"
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
    color: "from-yellow-400 to-yellow-600"
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
    color: "from-red-500 to-orange-600"
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
    color: "from-purple-500 to-pink-500"
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
    color: "from-blue-600 to-purple-600"
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
    color: "from-indigo-500 to-purple-600"
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
    color: "from-orange-500 to-red-500"
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
    color: "from-cyan-500 to-blue-600"
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
    color: "from-orange-600 to-red-700"
  }
};

export default function CleanTemplatesApp() {
  const [activeView, setActiveView] = useState('home');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const downloadFile = (lang) => {
    const file = FILES[lang];
    const blob = new Blob([file.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    a.click();
    URL.revokeObjectURL(url);
    
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const downloadAllFiles = () => {
    Object.keys(FILES).forEach((lang, index) => {
      setTimeout(() => downloadFile(lang), index * 200);
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Success Notification */}
      {showSuccess && (
        <div className="fixed top-4 right-4 z-50 bg-green-500 text-white px-6 py-3 rounded-lg shadow-xl flex items-center gap-2 animate-bounce">
          <Check className="w-5 h-5" />
          تم التحميل بنجاح! 🎉
        </div>
      )}

      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-xl bg-white/5">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Code className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Clean Templates</h1>
              <p className="text-xs text-purple-300">قوالب برمجية نظيفة</p>
            </div>
          </div>
          
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-white"
          >
            <Menu className="w-6 h-6" />
          </button>

          <nav className="hidden md:flex gap-4">
            <button
              onClick={() => setActiveView('home')}
              className={`px-4 py-2 rounded-lg transition ${
                activeView === 'home' 
                  ? 'bg-purple-500 text-white' 
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              الرئيسية
            </button>
            <button
              onClick={() => setActiveView('templates')}
              className={`px-4 py-2 rounded-lg transition ${
                activeView === 'templates' 
                  ? 'bg-purple-500 text-white' 
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              القوالب
            </button>
            <button
              onClick={() => setActiveView('why')}
              className={`px-4 py-2 rounded-lg transition ${
                activeView === 'why' 
                  ? 'bg-purple-500 text-white' 
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              لماذا؟
            </button>
          </nav>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-white/10 p-4">
            <div className="flex flex-col gap-2">
              <button onClick={() => { setActiveView('home'); setMobileMenuOpen(false); }} className="text-right text-purple-200 hover:bg-white/10 px-4 py-2 rounded-lg">الرئيسية</button>
              <button onClick={() => { setActiveView('templates'); setMobileMenuOpen(false); }} className="text-right text-purple-200 hover:bg-white/10 px-4 py-2 rounded-lg">القوالب</button>
              <button onClick={() => { setActiveView('why'); setMobileMenuOpen(false); }} className="text-right text-purple-200 hover:bg-white/10 px-4 py-2 rounded-lg">لماذا؟</button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-12">
        {activeView === 'home' && (
          <div className="space-y-12">
            {/* Hero Section */}
            <div className="text-center space-y-6">
              <div className="inline-flex items-center gap-2 bg-purple-500/20 border border-purple-500/30 rounded-full px-4 py-2 text-purple-300 text-sm">
                <Sparkles className="w-4 h-4" />
                قوة البساطة
              </div>
              
              <h2 className="text-5xl md:text-7xl font-bold text-white">
                قوالب برمجية
                <span className="block bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  نظيفة 100%
                </span>
              </h2>
              
              <p className="text-xl text-purple-200 max-w-2xl mx-auto">
                ابدأ مشاريعك البرمجية بقوالب احترافية خالية من التعقيدات
              </p>

              <div className="flex flex-wrap justify-center gap-4 pt-4">
                <button
                  onClick={() => setActiveView('templates')}
                  className="group bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:scale-105 transition flex items-center gap-2"
                >
                  تصفح القوالب
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition" />
                </button>
                
                <button
                  onClick={downloadAllFiles}
                  className="bg-white/10 backdrop-blur text-white border border-white/20 px-8 py-4 rounded-xl font-bold text-lg hover:bg-white/20 transition flex items-center gap-2"
                >
                  <Package className="w-5 h-5" />
                  تحميل الكل (10 ملفات)
                </button>
              </div>
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-4 gap-6 pt-12">
              {[
                { icon: X, title: 'بدون تعقيد', desc: 'صفر أكواد غير ضرورية' },
                { icon: Sparkles, title: 'بداية سريعة', desc: 'ابدأ البرمجة فوراً' },
                { icon: Code, title: 'تحكم كامل', desc: 'مشروعك، قواعدك' },
                { icon: Check, title: 'احترافي', desc: 'بنية معيارية متقنة' }
              ].map((feature, i) => (
                <div key={i} className="bg-white/5 backdrop-blur border border-white/10 rounded-xl p-6 hover:bg-white/10 transition">
                  <feature.icon className="w-10 h-10 text-purple-400 mb-4" />
                  <h3 className="text-white font-bold text-lg mb-2">{feature.title}</h3>
                  <p className="text-purple-300 text-sm">{feature.desc}</p>
                </div>
              ))}
            </div>

            {/* Languages Preview */}
            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
              <h3 className="text-2xl font-bold text-white mb-6 text-center">اللغات المتاحة</h3>
              <div className="flex flex-wrap justify-center gap-4">
                {Object.entries(FILES).map(([key, file]) => (
                  <div key={key} className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-lg">
                    <span className="text-2xl">{file.emoji}</span>
                    <span className="text-white text-sm">{file.desc.replace('Clean ', '').replace(' Template', '')}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeView === 'templates' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-white mb-4">اختر قالبك</h2>
              <p className="text-purple-300">كل قالب احترافي، نظيف، وجاهز للاستخدام</p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(FILES).map(([key, file]) => (
                <div
                  key={key}
                  className="group bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition cursor-pointer"
                  onClick={() => setSelectedTemplate(key)}
                >
                  <div className={`w-16 h-16 bg-gradient-to-br ${file.color} rounded-xl flex items-center justify-center text-3xl mb-4 group-hover:scale-110 transition`}>
                    {file.emoji}
                  </div>
                  
                  <h3 className="text-xl font-bold text-white mb-2">{file.desc}</h3>
                  <p className="text-purple-300 text-sm mb-4">{file.name}</p>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadFile(key);
                    }}
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg font-bold hover:scale-105 transition flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    تحميل
                  </button>
                </div>
              ))}
            </div>

            {selectedTemplate && (
              <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-40" onClick={() => setSelectedTemplate(null)}>
                <div className="bg-slate-800 border border-white/20 rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                      <span className="text-3xl">{FILES[selectedTemplate].emoji}</span>
                      {FILES[selectedTemplate].desc}
                    </h3>
                    <button onClick={() => setSelectedTemplate(null)} className="text-white hover:bg-white/10 p-2 rounded-lg">
                      <X className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <pre className="bg-black/50 text-green-400 p-4 rounded-lg overflow-x-auto text-sm mb-4 font-mono">
                    {FILES[selectedTemplate].content}
                  </pre>
                  
                  <button
                    onClick={() => downloadFile(selectedTemplate)}
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg font-bold hover:scale-105 transition flex items-center justify-center gap-2"
                  >
                    <Download className="w-5 h-5" />
                    تحميل {FILES[selectedTemplate].name}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeView === 'why' && (
          <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-white mb-4">لماذا القوالب النظيفة؟</h2>
              <p className="text-purple-300">الفرق بين البداية الصحيحة والوقت الضائع</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <X className="w-8 h-8 text-red-400" />
                  <h3 className="text-2xl font-bold text-white">القوالب التقليدية</h3>
                </div>
                <ul className="space-y-3 text-red-300">
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>ممتلئة بأكواد تجريبية ستحذفها</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>مليئة بمكتبات لن تستخدمها</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>تضيع وقتك في الحذف والتنظيف</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">❌</span>
                    <span>محيرة للمبتدئين</span>
                  </li>
                </ul>
              </div>

              <div className="bg-green-500/10 border border-green-500/30 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Check className="w-8 h-8 text-green-400" />
                  <h3 className="text-2xl font-bold text-white">قوالبنا النظيفة</h3>
                </div>
                <ul className="space-y-3 text-green-300">
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">✅</span>
                    <span>نظيفة 100% - فقط البنية الأساسية</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">✅</span>
                    <span>جاهزة للكتابة فوراً</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">✅</span>
                    <span>أنت تتحكم بكل شيء</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">✅</span>
                    <span>بدون تشتيت أو تعقيد</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-2xl p-8 text-center">
              <Sparkles className="w-12 h-12 text-purple-400 mx-auto mb-4" />
              <p className="text-2xl text-white font-bold mb-4">
                "أفضل كود هو الذي تكتبه بنفسك!"
              </p>
              <p className="text-purple-300">
                قوالبنا مثل لوحة بيضاء للرسامين - نقطة البداية المثالية للمبرمجين
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 mt-20">
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p className="text-purple-300">
            صنع بـ 💜 من أجل المبرمجين الذين يحبون البساطة
          </p>
          <p className="text-purple-400 text-sm mt-2">
            Clean Templates © 2025 - ابدأ نظيفاً، ابنِ عظيماً
          </p>
        </div>
      </footer>
    </div>
  );
}
