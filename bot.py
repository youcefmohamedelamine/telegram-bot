import React, { useState } from 'react';
import { Send, CheckCircle, AlertCircle, Clock, User, DollarSign, Package } from 'lucide-react';

export default function TelegramBotDashboard() {
  const [orders, setOrders] = useState([
    { id: '123456789', freeFireId: 'FF_7891234', amount: 500, status: 'completed', time: '2025-10-05 14:30' },
    { id: '987654321', freeFireId: 'FF_4567890', amount: 1000, status: 'waiting_id', time: '2025-10-05 15:45' },
    { id: '456789123', freeFireId: 'FF_1234567', amount: 250, status: 'completed', time: '2025-10-05 16:20' }
  ]);

  const [selectedOrder, setSelectedOrder] = useState(null);
  const [message, setMessage] = useState('');

  const statusConfig = {
    completed: { color: 'bg-green-500', icon: CheckCircle, text: 'مكتمل', textColor: 'text-green-700' },
    waiting_id: { color: 'bg-yellow-500', icon: Clock, text: 'بانتظار ID', textColor: 'text-yellow-700' },
    processing: { color: 'bg-blue-500', icon: Package, text: 'قيد المعالجة', textColor: 'text-blue-700' }
  };

  const totalRevenue = orders.reduce((sum, order) => sum + order.amount, 0);
  const completedOrders = orders.filter(o => o.status === 'completed').length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6 border-t-4 border-purple-500">
          <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center gap-3">
            <span className="text-purple-600">🎮</span>
            لوحة تحكم بوت فري فاير
          </h1>
          <p className="text-gray-600">إدارة الطلبات والمدفوعات بسهولة</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm mb-1">إجمالي الطلبات</p>
                <p className="text-4xl font-bold">{orders.length}</p>
              </div>
              <Package className="w-12 h-12 opacity-80" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm mb-1">الطلبات المكتملة</p>
                <p className="text-4xl font-bold">{completedOrders}</p>
              </div>
              <CheckCircle className="w-12 h-12 opacity-80" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm mb-1">إجمالي الإيرادات</p>
                <p className="text-4xl font-bold">{totalRevenue}</p>
                <p className="text-blue-100 text-xs">دينار جزائري</p>
              </div>
              <DollarSign className="w-12 h-12 opacity-80" />
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6">
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              📋 قائمة الطلبات
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">معرف المستخدم</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">Free Fire ID</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المبلغ</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الوقت</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {orders.map((order, index) => {
                  const status = statusConfig[order.status];
                  const StatusIcon = status.icon;
                  return (
                    <tr key={index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-gray-400" />
                          <span className="font-mono text-sm text-gray-700">{order.id}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-sm font-semibold text-purple-600">{order.freeFireId}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-bold text-green-600">{order.amount} دج</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${status.textColor} bg-${status.color.split('-')[1]}-100`}>
                          <StatusIcon className="w-3 h-3" />
                          {status.text}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        <Clock className="w-4 h-4 inline ml-1" />
                        {order.time}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setSelectedOrder(order)}
                          className="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:shadow-lg transition-all"
                        >
                          إرسال رسالة
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Message Modal */}
        {selectedOrder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-gray-800">إرسال رسالة</h3>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4 mb-4">
                <p className="text-sm text-gray-600 mb-1">إلى المستخدم:</p>
                <p className="font-mono font-bold text-purple-700">{selectedOrder.id}</p>
              </div>

              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="اكتب رسالتك هنا..."
                className="w-full border-2 border-gray-200 rounded-xl p-4 mb-4 focus:border-purple-500 focus:outline-none resize-none"
                rows="4"
              />

              <button
                onClick={() => {
                  alert(`تم إرسال الرسالة إلى ${selectedOrder.id}`);
                  setSelectedOrder(null);
                  setMessage('');
                }}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl font-bold hover:shadow-lg transition-all flex items-center justify-center gap-2"
              >
                <Send className="w-5 h-5" />
                إرسال الرسالة
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
