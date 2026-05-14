<script lang="ts">
</script>

<h2>このサイトについて</h2>

<section class="lead">
  <p>
    <strong>世田谷区議会QAナビ</strong> は、世田谷区議会の会議録を「質問者と答弁者の
    やり取り（QA）」単位に整理し、市民が一つひとつに対して
    <em>共感／重要度</em> を付けて振り返ることができる非公式の試作サービスです。
  </p>
</section>

<section>
  <h3>🎯 何のためのサイト？</h3>
  <p>
    議員の選挙公報やSNS発信は政策を端的に示してくれますが、実際の議会で
    どう発言したかまで追えている有権者は多くありません。とはいえ会議録の
    原文は長く、論点ごとに切り出された読みやすい入口があると助けになる
    はず――そんな問題意識から作っています。
  </p>
  <p>
    投票や政治的判断の代替になることを目指してはいません。あくまで
    <em>「公開情報を少し見やすくする」</em> 補助ツールという位置付けです。
  </p>
</section>

<section>
  <h3>🧩 できること</h3>
  <ul>
    <li><strong>QA を1件ずつ表示</strong>：論点の前提（議題説明）と質疑応答を分けて読めます。</li>
    <li><strong>評価する</strong>：各QAに「共感度（-3〜+3）」と「重要度（0〜3）」を付けられます。</li>
    <li><strong>統計を見る</strong>：自分の評価傾向を議員別／会派別に集計し、信頼区間付きで可視化します。</li>
    <li><strong>論点マップ</strong>：委員会間の議員の重なりや評価の偏りをグラフで俯瞰できます。</li>
    <li><strong>履歴の管理</strong>：自分が評価したQAを後から見返したり、CSVで書き出し／取り込みができます。</li>
    <li><strong>テーマ切替</strong>：プレーン／チャット／和風／サイバーパンクから外観を選べます。</li>
  </ul>
</section>

<section>
  <h3>🔒 評価データの扱い</h3>
  <ul>
    <li>あなたの評価は <strong>すべてあなたのブラウザ内（IndexedDB）にだけ保存</strong> されます。</li>
    <li>サーバーには <strong>一切送信されません</strong>。本サイトに評価を集計するためのバックエンドはありません。</li>
    <li>ブラウザのデータを消去すると評価も消えます。残しておきたい場合は履歴ページから CSV で書き出してください。</li>
    <li>会議録データそのものは、週次で公開元から自動取得した <strong>静的JSON</strong> としてCDN配信しています。</li>
  </ul>
</section>

<section>
  <h3>⚠️ 使う前に知っておいてほしいこと</h3>
  <ul>
    <li>
      本サイトは <strong>有志による非公式</strong> のものであり、世田谷区および
      世田谷区議会の公式サービス・公式見解ではありません。
    </li>
    <li>
      会議録を機械的に「QA」へ切り分けて表示しています。区切り方や発言者の
      対応付けには <strong>処理上の誤りが含まれる可能性</strong> があります。
      正確な内容は必ず原文（出典）でご確認ください。
    </li>
    <li>
      表示対象はおおむね <strong>直近4年分</strong> の会議録に限定しています。
      それ以前の発言は本サイトでは扱っていません。
    </li>
    <li>
      評価の対象は「会議録に残った発言」だけです。会議外の活動・調整・票の
      行方など、議員の仕事の多くはここには現れません。
    </li>
    <li>
      議事の進行や答弁の都合で、ある議員が <strong>得意分野でしか発言していない</strong>
      ような偏りも生じえます。少数の評価結果から議員の良し悪しを断ずる
      用途には適していません。
    </li>
    <li>
      口頭の巧拙が評価に影響する点にも留意してください。読み手としても
      バイアスを意識しておくと健全です。
    </li>
  </ul>
</section>

<section>
  <h3>📚 データ出典</h3>
  <ul>
    <li>
      <a href="https://www.city.setagaya.lg.jp/gikai/index.html" target="_blank" rel="noopener noreferrer">
        世田谷区議会（区公式ホームページ）
      </a>
    </li>
    <li>
      <a href="https://kugi.city.setagaya.tokyo.jp/voices/" target="_blank" rel="noopener noreferrer">
        世田谷区議会 会議録検索システム
      </a>
    </li>
  </ul>
  <p class="hint">
    会議録は議会から公開されている公的記録です。本サイトはそれを構造化して
    再表示しているもので、原文の改変は行っていません（個人情報に類する語の
    伏字化は行っています）。
  </p>
</section>

<section>
  <h3>🛠️ お問い合わせ・削除依頼</h3>
  <p>
    誤った表示の指摘、削除の依頼、機能要望などは
    <a href="https://github.com/Luis8492/ZeroTrustDemocracy/issues" target="_blank" rel="noopener noreferrer">
      GitHub Issues
    </a>
    にお寄せください。
  </p>
</section>

<style>
  h2 {
    margin: 0 0 1rem;
  }
  h3 {
    margin: 1.75rem 0 0.5rem;
    font-size: 1.05rem;
  }
  section {
    margin-bottom: 1.25rem;
  }
  .lead {
    border-left: 3px solid var(--accent);
    padding: 0.5rem 0 0.5rem 1rem;
    color: var(--text);
    background: color-mix(in srgb, var(--accent) 6%, transparent);
    border-radius: 4px;
  }
  .lead p { margin: 0; }
  ul {
    margin: 0.25rem 0 0.5rem;
    padding-left: 1.25rem;
  }
  li { margin: 0.3rem 0; line-height: 1.6; }
  p { line-height: 1.7; }
  .hint {
    color: var(--text-muted);
    font-size: 0.9rem;
  }
  a {
    color: var(--accent);
  }

  :global([data-theme='hud']) .lead {
    border-left-color: var(--accent);
    box-shadow: inset 0 0 12px rgba(0, 240, 255, 0.08);
  }
  :global([data-theme='scroll']) .lead {
    border-left-color: var(--accent);
    font-family: var(--font-display);
    letter-spacing: 0.03em;
  }
</style>
