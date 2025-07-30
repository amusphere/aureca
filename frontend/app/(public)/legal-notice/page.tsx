import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '特定商取引法に基づく表記',
  description: '特定商取引法に基づく表記 - 合同会社アミュスフィア',
};

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-sm rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            特定商取引法に基づく表記
          </h1>

          <div className="space-y-6">
            {/* 販売業者名 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">販売業者名</dt>
              <dd className="text-gray-700">合同会社アミュスフィア</dd>
            </div>

            {/* 運営統括責任者 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">運営統括責任者</dt>
              <dd className="text-gray-700">島袋秀音</dd>
            </div>

            {/* 所在地 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">所在地</dt>
              <dd className="text-gray-700">
                〒900-0016 沖縄県那覇市前島３丁目２５番２号 泊ポートビル１階
              </dd>
            </div>

            {/* 電話番号 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">電話番号</dt>
              <dd className="text-gray-700">070-4152-7790</dd>
            </div>

            {/* 受付時間 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">受付時間</dt>
              <dd className="text-gray-700">10:00〜18:00（土日祝を除く）</dd>
            </div>

            {/* 販売価格 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">販売価格</dt>
              <dd className="text-gray-700">
                各サブスクリプションプランのページに税込価格を表示します。
              </dd>
            </div>

            {/* 追加手数料等の追加料金 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">追加手数料等の追加料金</dt>
              <dd className="text-gray-700">
                <div>消費税（価格が税込表示の場合を除く）</div>
                <div>インターネット接続に伴う通信費（お客様負担）</div>
              </dd>
            </div>

            {/* 受け付け可能な決済手段 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">受け付け可能な決済手段</dt>
              <dd className="text-gray-700">
                クレジットカード（Stripe 決済）
              </dd>
            </div>

            {/* 決済期間 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">決済期間</dt>
              <dd className="text-gray-700">
                <div>初回：ご登録手続き完了時に課金されます。</div>
                <div>以降：ご契約プランの更新日に自動で課金されます。次回請求日はマイページでご確認いただけます。</div>
              </dd>
            </div>

            {/* 引渡時期 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">引渡時期</dt>
              <dd className="text-gray-700">
                決済完了後、即時にご利用いただけます。
              </dd>
            </div>

            {/* 交換および返品（返金ポリシー） */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">交換および返品（返金ポリシー）</dt>
              <dd className="text-gray-700">
                <div>デジタルサービスの性質上、購入後の返金はお受けしておりません。</div>
                <div>解約をご希望の場合、次回請求日の前日までにマイページの「プラン管理」から手続きを行ってください。解約完了後、次回以降の課金は発生しません。</div>
                <div>利用期間途中での解約による日割り返金は行っておりません。</div>
              </dd>
            </div>

            {/* 不良品の取扱い */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">不良品の取扱い</dt>
              <dd className="text-gray-700">
                システム障害等によりサービスを正常に利用できない場合は、当社が定める規約に基づき対応いたします。
              </dd>
            </div>

            {/* 申込み期間の制限 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">申込み期間の制限</dt>
              <dd className="text-gray-700">特に制限はございません。</dd>
            </div>

            {/* 販売数量の制限 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">販売数量の制限</dt>
              <dd className="text-gray-700">制限は設けておりません。</dd>
            </div>

            {/* 動作推奨環境 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">動作推奨環境</dt>
              <dd className="text-gray-700">
                最新バージョンの Google Chrome／Safari／Microsoft Edge／Firefox
              </dd>
            </div>

            {/* 特別な販売条件 */}
            <div className="flex">
              <dt className="w-48 flex-shrink-0 font-semibold text-gray-900">特別な販売条件</dt>
              <dd className="text-gray-700">
                <div>無料トライアルをご利用の場合、トライアル期間終了と同時に有料プランへ自動移行し課金されます。</div>
                <div>最短利用期間の定めはありません。</div>
              </dd>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
