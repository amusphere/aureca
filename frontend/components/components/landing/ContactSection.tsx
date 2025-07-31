import { MailIcon } from "lucide-react";

export default function ContactSection() {
  return (
    <section id="contact" className="py-16 sm:py-24 bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-6">
          お問い合わせ
        </h2>
        <p className="text-base sm:text-lg text-gray-600 mb-12 px-4">
          ご質問やご相談がございましたら、お気軽にメールでお問い合わせください。
        </p>

        <div className="bg-white rounded-3xl p-6 sm:p-8 lg:p-12 shadow-sm border border-gray-200 max-w-2xl mx-auto">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center">
              <MailIcon className="w-8 h-8 text-white" />
            </div>
            <div className="text-center sm:text-left">
              <h3 className="text-lg sm:text-xl font-bold text-gray-900">メールアドレス</h3>
              <a
                href="mailto:info@amusphere.dev"
                className="text-base sm:text-lg text-blue-600 hover:text-blue-700 transition-colors break-all"
              >
                info@amusphere.dev
              </a>
            </div>
          </div>

          <p className="text-gray-600">
            通常2営業日以内にご返信いたします。<br />
            お気軽にお問い合わせください。
          </p>
        </div>
      </div>
    </section>
  );
}