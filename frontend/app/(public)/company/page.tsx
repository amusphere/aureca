import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '会社概要 - 合同会社アミュスフィア',
  description: '合同会社アミュスフィアの会社概要、事業内容をご紹介します。',
};

export default function CompanyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-sm rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            会社概要
          </h1>

          <div className="space-y-8">
            {/* 基本情報 */}
            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-4">基本情報</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <dt className="font-semibold text-gray-900">会社名</dt>
                    <dd className="text-gray-700">合同会社アミュスフィア</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-gray-900">英文社名</dt>
                    <dd className="text-gray-700">Amusphere LLC</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-gray-900">設立</dt>
                    <dd className="text-gray-700">2020年</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-gray-900">所在地</dt>
                    <dd className="text-gray-700">
                      〒900-0016<br />
                      沖縄県那覇市前島３丁目２５番２号<br />
                      泊ポートビル１階
                    </dd>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <dt className="font-semibold text-gray-900">事業内容</dt>
                    <dd className="text-gray-700">
                      <ul className="list-disc list-inside space-y-1">
                        <li>AIソフトウェアの開発・運営</li>
                        <li>タスク管理システムの提供</li>
                        <li>生産性向上ツールの開発</li>
                        <li>ITコンサルティング</li>
                      </ul>
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-gray-900">お問い合わせ</dt>
                    <dd className="text-gray-700">
                      <a href="mailto:info@amusphere.dev" className="text-blue-600 hover:text-blue-700">
                        info@amusphere.dev
                      </a>
                    </dd>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}