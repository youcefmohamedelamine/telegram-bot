from flask import Flask, render_template_string, jsonify, request
import os

app = Flask(__name__)

STAR_PRICE = 999

templates_data = {
    "python": {
        "name": "main.py",
        "emoji": "🐍",
        "desc": "Python النظيف",
        "joke": "الملف الوحيد الذي لن يرميه الـ garbage collector! 🗑️",
        "content": """# Python Clean Template
# Zero bloat. Pure simplicity.

def main():
    pass

if __name__ == "__main__":
    main()
"""
    },
    "javascript": {
        "name": "index.js",
        "emoji": "💛",
        "desc": "JavaScript الصافي",
        "joke": "بدون undefined، بدون null، بس أنت ومشاكلك! 😅",
        "content": """// JavaScript Clean Template
// No frameworks. No dependencies.

function main() {
    // Your code here
}

main();
"""
    },
    "java": {
        "name": "Main.java",
        "emoji": "☕",
        "desc": "Java المركز",
        "joke": "3 مليار جهاز يشغلون Java... وأنت بعدك ما بلشت! ⏰",
        "content": """// Java Clean Template

public class Main {
    public static void main(String[] args) {
        // Your code here
    }
}
"""
    },
    "cpp": {
        "name": "main.cpp",
        "emoji": "⚡",
        "desc": "C++ السريع",
        "joke": "سريع لدرجة إنه بيخلص قبل ما تفهم الكود! 🏃‍♂️",
        "content": """// C++ Clean Template

#include <iostream>
using namespace std;

int main() {
    // Your code here
    return 0;
}
"""
    },
    "csharp": {
        "name": "Program.cs",
        "emoji": "🔷",
        "desc": "C# الاحترافي",
        "joke": "Microsoft وافقت عليه شخصياً! (مش حقيقي بس يبان كويس) 🎭",
        "content": """// C# Clean Template

using System;

class Program
{
    static void Main(string[] args)
    {
        // Your code here
    }
}
"""
    },
    "php": {
        "name": "index.php",
        "emoji": "🐘",
        "desc": "PHP الجديد",
        "joke": "نعم، الناس لسا بتستعمل PHP في 2025! 🦕",
        "content": """<?php
// PHP Clean Template

function main() {
    // Your code here
}

main();
?>
"""
    },
    "html": {
        "name": "index.html",
        "emoji": "🌐",
        "desc": "HTML النقي",
        "joke": "بدون Bootstrap! نعم، هتكتب كل حاجة بإيدك يا بطل! 💪",
        "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clean HTML</title>
</head>
<body>
    <!-- Your content here -->
</body>
</html>
"""
    },
    "css": {
        "name": "style.css",
        "emoji": "🎨",
        "desc": "CSS الفاضي",
        "joke": "مش هنحط !important في كل سطر، وعد! 🤞",
        "content": """/* CSS Clean Template */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Your styles here */
"""
    },
    "go": {
        "name": "main.go",
        "emoji": "🔵",
        "desc": "Go المنطلق",
        "joke": "Google عملته عشان محدش يفهم C++ تاني! 🤯",
        "content": """// Go Clean Template

package main

import "fmt"

func main() {
    // Your code here
    fmt.Println("Ready!")
}
"""
    },
    "rust": {
        "name": "main.rs",
        "emoji": "🦀",
        "desc": "Rust الآمن",
        "joke": "الـ Compiler هيزعلك قبل ما البرنامج يشتغل! 😤",
        "content": """// Rust Clean Template

fn main() {
    // Your code here
    println!("Ready!");
}
"""
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر القوالب النظيفة 😂</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover:hover { transform: translateY(-5px); }
    </style>
</head>
<body class="bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white min-h-screen">
    
    <!-- Header -->
    <header class="bg-black bg-opacity-50 backdrop-blur-md p-6 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div class="text-4xl">💻</div>
                <div>
                    <h1 class="text-3xl font-bold">متجر القوالب "النظيفة" 😂</h1>
                    <p class="text-sm text-gray-300">لأن الكود الفاضي أحسن من الكود الغلط!</p>
                </div>
            </div>
            <div id="cart-badge" class="bg-purple-600 px-4 py-2 rounded-full font-bold">
                🛒 <span id="cart-count">0</span>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-6 py-12">
        
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-3xl p-8 text-center text-black mb-12">
            <h2 class="text-4xl font-bold mb-4">🎉 العرض الخرافي!</h2>
            <p class="text-2xl mb-6">10 ملفات فاضية تماماً بـ ⭐{{ price * 10 }} نجمة فقط!</p>
            <button onclick="buyBundle()" class="bg-black text-white px-8 py-4 rounded-full text-xl font-bold hover:bg-gray-800 transition-all transform hover:scale-105">
                📦 اشتري الباقة الكاملة (وفر 0%)
            </button>
            <p class="text-sm mt-3">* التوفير وهمي، بس الملفات حقيقية! 😉</p>
        </div>

        <!-- Funny Reasons -->
        <div class="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl p-8 mb-12">
            <h3 class="text-3xl font-bold mb-6 text-center">😂 ليه القوالب النظيفة؟</h3>
            <div class="grid md:grid-cols-2 gap-4">
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🎪 لأن حياتك محتاجة شوية فضاء... في الكود على الأقل!</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🍕 أخف من بيتزا دومينوز (بس أغلى شوية)</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🎭 مكتوب بحب... ومسح بحب أكتر!</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🌟 الملفات دي فاضية لدرجة إنها فلسفية!</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🎪 كل المبرمجين المشهورين بدأوا من صفحة بيضا (أو كذبوا)</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🎨 أحسن من لوحة بيكاسو... على الأقل دي بتشتغل!</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🚀 ناسا بتستخدمها (في أحلامنا)</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">💎 نظيفة لدرجة إن Marie Kondo هتفرح!</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🎯 الكود الوحيد اللي مش فيه bugs... لسه!</div>
                <div class="bg-black bg-opacity-30 p-4 rounded-xl">🏆 فازت بجائزة 'أفضل ملف فاضي' 3 سنين متتالية!</div>
            </div>
        </div>

        <!-- Templates Grid -->
        <div id="templates-grid" class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% for lang, template in templates.items() %}
            <div class="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl p-6 card-hover transition-all transform cursor-pointer"
                 onclick="showDetails('{{ lang }}')">
                <div class="text-6xl mb-4 text-center">{{ template.emoji }}</div>
                <h3 class="text-2xl font-bold mb-2 text-center">{{ template.desc }}</h3>
                <p class="text-yellow-300 text-center mb-4 min-h-[60px]">{{ template.joke }}</p>
                <button onclick="event.stopPropagation(); addToCart('{{ lang }}')" 
                        id="btn-{{ lang }}"
                        class="w-full bg-purple-600 hover:bg-purple-700 py-3 rounded-xl font-bold transition-all">
                    ⭐{{ price }}
                </button>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Cart Summary (Fixed) -->
    <div id="cart-summary" class="hidden fixed bottom-6 left-6 bg-purple-600 rounded-2xl p-6 shadow-2xl max-w-sm">
        <h3 class="text-xl font-bold mb-3">🛒 سلة المشتريات</h3>
        <div id="cart-items" class="space-y-2 mb-4"></div>
        <div class="border-t border-white border-opacity-30 pt-3 mb-3">
            <div class="flex justify-between items-center text-xl font-bold">
                <span>المجموع:</span>
                <span class="text-yellow-400" id="total-price">⭐0</span>
            </div>
        </div>
        <button onclick="checkout()" class="w-full bg-yellow-400 text-black py-3 rounded-xl font-bold hover:bg-yellow-300 transition-all">
            ⚡ اشتري الآن!
        </button>
    </div>

    <!-- Details Modal -->
    <div id="details-modal" class="hidden fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4" onclick="closeModal()">
        <div class="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full" onclick="event.stopPropagation()">
            <div class="text-center mb-6">
                <div id="modal-emoji" class="text-8xl mb-4"></div>
                <h2 id="modal-title" class="text-3xl font-bold mb-2"></h2>
                <p id="modal-joke" class="text-yellow-300 text-xl"></p>
            </div>
            <div class="bg-black rounded-xl p-6 mb-6">
                <pre id="modal-code" class="text-green-400 text-sm overflow-x-auto"></pre>
            </div>
            <div class="flex gap-4">
                <button onclick="addFromModal()" class="flex-1 bg-purple-600 hover:bg-purple-700 py-3 rounded-xl font-bold transition-all">
                    أضف للسلة ⭐{{ price }}
                </button>
                <button onclick="closeModal()" class="px-6 bg-gray-700 hover:bg-gray-600 py-3 rounded-xl font-bold transition-all">
                    إغلاق
                </button>
            </div>
        </div>
    </div>

    <!-- Success Modal -->
    <div id="success-modal" class="hidden fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
        <div class="bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl p-8 max-w-md w-full text-center">
            <div class="text-6xl mb-4">🎉</div>
            <h2 class="text-3xl font-bold mb-4">مبروك!</h2>
            <p id="success-message" class="text-xl mb-6"></p>
            <div class="bg-white bg-opacity-20 rounded-xl p-4 mb-6">
                <p class="text-2xl font-bold mb-2">المجموع المدفوع:</p>
                <p id="paid-amount" class="text-4xl font-bold text-yellow-300"></p>
            </div>
            <button onclick="closeSuccess()" class="w-full bg-white text-black py-3 rounded-xl font-bold hover:bg-gray-200 transition-all">
                رجوع للصفحة الرئيسية
            </button>
            <p class="text-xs mt-4 text-gray-200">* هذا تطبيق تجريبي، لا يوجد دفع حقيقي (للأسف) 💸</p>
        </div>
    </div>

    <footer class="bg-black bg-opacity-50 backdrop-blur-md mt-20 py-8">
        <div class="max-w-7xl mx-auto px-6 text-center">
            <p class="text-xl mb-4">💡 <strong>نصيحة الخبراء:</strong> الكود الفاضي أسهل في الصيانة من الكود المليان bugs!</p>
            <p class="text-sm text-gray-400">© 2025 متجر القوالب النظيفة | كل الحقوق محفوظة (حتى لو الملفات فاضية) 😄</p>
        </div>
    </footer>

    <script>
        const templates = {{ templates_json | safe }};
        const STAR_PRICE = {{ price }};
        let cart = [];
        let currentLang = null;

        function addToCart(lang) {
            if (!cart.includes(lang)) {
                cart.push(lang);
                updateCart();
            }
        }

        function removeFromCart(lang) {
            cart = cart.filter(l => l !== lang);
            updateCart();
        }

        function updateCart() {
            document.getElementById('cart-count').textContent = cart.length;
            
            if (cart.length > 0) {
                document.getElementById('cart-summary').classList.remove('hidden');
                
                const cartItems = document.getElementById('cart-items');
                cartItems.innerHTML = cart.map(lang => `
                    <div class="flex items-center gap-2 bg-black bg-opacity-30 p-2 rounded-lg">
                        <span class="text-2xl">${templates[lang].emoji}</span>
                        <span class="flex-1">${templates[lang].name}</span>
                        <button onclick="removeFromCart('${lang}')" class="text-red-400 hover:text-red-300">✕</button>
                    </div>
                `).join('');
                
                const total = cart.length === 10 ? STAR_PRICE * 10 : cart.length * STAR_PRICE;
                document.getElementById('total-price').textContent = `⭐${total}`;
                
                // Update buttons
                cart.forEach(lang => {
                    const btn = document.getElementById(`btn-${lang}`);
                    if (btn) {
                        btn.textContent = '✓ في السلة';
                        btn.classList.add('bg-green-600');
                        btn.classList.remove('bg-purple-600');
                    }
                });
            } else {
                document.getElementById('cart-summary').classList.add('hidden');
            }
        }

        function buyBundle() {
            cart = Object.keys(templates);
            updateCart();
            checkout();
        }

        function showDetails(lang) {
            currentLang = lang;
            const template = templates[lang];
            document.getElementById('modal-emoji').textContent = template.emoji;
            document.getElementById('modal-title').textContent = template.desc;
            document.getElementById('modal-joke').textContent = template.joke;
            document.getElementById('modal-code').textContent = template.content;
            document.getElementById('details-modal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('details-modal').classList.add('hidden');
            currentLang = null;
        }

        function addFromModal() {
            if (currentLang) {
                addToCart(currentLang);
                closeModal();
            }
        }

        function checkout() {
            const total = cart.length === 10 ? STAR_PRICE * 10 : cart.length * STAR_PRICE;
            const count = cart.length;
            
            document.getElementById('success-message').innerHTML = 
                `اشتريت ${count} ملف فاضي بنجاح!<br>(كان ممكن تعملهم بنفسك بس خلينا نتفائل 😂)`;
            document.getElementById('paid-amount').textContent = `⭐${total}`;
            document.getElementById('success-modal').classList.remove('hidden');
        }

        function closeSuccess() {
            document.getElementById('success-modal').classList.add('hidden');
            cart = [];
            updateCart();
            location.reload();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    import json
    return render_template_string(
        HTML_TEMPLATE, 
        templates=templates_data, 
        price=STAR_PRICE,
        templates_json=json.dumps(templates_data)
    )

@app.route('/api/templates')
def get_templates():
    return jsonify(templates_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
