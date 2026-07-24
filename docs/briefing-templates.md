# Briefing Templates
## tech-intel

Two delivery styles for the daily Telegram briefing. The system auto-selects based on a user preference flag in `.env`. Both contain identical signals — only the tone, depth of explanation, and framing differ.

---

## Style 1 — Professional (Brief)

For when you're already familiar with the context and want fast, dense signal.

**Characteristics:**
- No hand-holding explanations
- Entity names dropped without introduction
- Shorter per-signal blocks
- Prediction framing is analytical, not narrative
- Giant Watch is one line per company, no elaboration

---

### Template: Professional Style

```
Tech Intel — [DAY], [DATE]

CALLBACKS
[EMOJI] [STATUS] ([DATE]) — [one-line recap of what was predicted] → [what happened today]
Accuracy this week: [X/Y] ([%])

---

[DOMAIN EMOJI] [DOMAIN] · #[N]
[Headline]
[URL]

[2-3 sentence plain summary. No jargon defined. Entities named directly.]
History: [one-line connection to prior signal if exists]
Prediction: [one forward-looking sentence]
Entities: [Entity1] · [Entity2] · [Entity3]

---

[ repeat for each signal ]

---

GIANT WATCH
[EMOJI] [Company] — [one line. key event or "no major news".]
[ repeat for each tracked company ]

---

[One sharp question or observation. One sentence.]

---
[N] ingested · [N] surfaced · Ollama [checkmark/cross] · Accuracy [X/Y]
```

---

## Style 2 — Beginner Friendly

For when you're still building context and need things explained from first principles. Assumes you know nothing about the companies, events, or terminology mentioned.

**Characteristics:**
- Every entity introduced with a one-line "who is this" on first mention
- "What this means" written like explaining to a smart friend, not a colleague
- "Why it matters to you" always personal and direct
- History connections spell out why the connection matters
- Predictions explained with reasoning, not just assertion
- Giant Watch includes a one-liner on what each company does

---

### Template: Beginner-Friendly Style

```
Tech Intel Briefing — [DAY], [DATE]

━━━━━━━━━━━━━━━━━━━━━━━━━━━

TODAY'S PICTURE
[N] signals · [N] history callbacks · [N] prediction updates · [N] new predictions

━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEFORE YOU READ — WHAT WE CALLED
These are things we predicted in earlier briefings. Today either confirmed them,
contradicted them, or we're still watching.

[EMOJI] [STATUS] ([DATE PREDICTED])
We said: [exact prediction text from that day]
Today: [what actually happened]
[If confirmed]: This is what confirmation looks like — [brief explanation of why this matters]
[If wrong]: We got this wrong because [reason]. Updated thinking: [revised view]
[If watching]: Still no movement. Keeping this flagged because [reason].

Running prediction accuracy: [X/Y] ([%]) since [start date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━

[DOMAIN EMOJI] [DOMAIN] · Signal #[N]
[Headline exactly as published]
[URL to original article]

What this means:
[2-4 sentences. Explain what happened in plain English. Define any term that might
be unfamiliar. Introduce any company or person on first mention with a brief
"who is this" parenthetical. No assumed knowledge.]

Why it matters to you:
[2-3 sentences. Make this personal and direct. Connect to broader patterns
the user is building. Use "you" language. Frame in terms of what changes
in the world because of this.]

Connected to history:
[If applicable: "On [DATE] we flagged [X]. Today's signal is directly related
because [reason]. This is a [N]-day pattern."]
[If no history: omit this section entirely]

What we predict next:
[1-2 sentences. A specific, falsifiable prediction. Include a timeframe.
Explain the reasoning briefly so it can be evaluated later.]

Entities: [Entity1] · [Entity2] · [Entity3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ repeat signal block for each signal ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━

GIANT WATCH
Companies we always track, regardless of whether they made the top signals today.
Even quiet days leave a trace.

[EMOJI] [Company] ([what this company does in 5 words])
[One line: key event today, or "No major news. [One notable background fact — stock move, ongoing case, recent hire]."]

━━━━━━━━━━━━━━━━━━━━━━━━━━━

ONE QUESTION WORTH SITTING WITH
[One question synthesized from today's signals. Not a news question — a
structural or strategic question about how the tech ecosystem works.
Designed to make you think, not just inform.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━
[N] signals ingested · [N] surfaced · Ollama [checkmark/cross]
Prediction accuracy this week: [X/Y] ([%])
```

---

## Full End-to-End Example

Below is a complete example of both styles for the same fictional briefing day.
All signals, predictions, and entities are illustrative.

---

### Example: Professional Style

```
Tech Intel — Friday, 25 Jul 2026

CALLBACKS
✅ CONFIRMED (Jul 22) — Anthropic hiring surge predicted Google infra deal → confirmed today
⏳ WATCHING (Jul 20) — EU Nvidia chip dominance review, still pending
Accuracy this week: 7/11 (64%)

---

💰 CAPITAL · #1
Microsoft invests $1.5B in UAE AI firm G42
https://reuters.com/technology/microsoft-g42-investment

G42 is Abu Dhabi's state-backed AI champion with prior Huawei ties. MS cleared
US Commerce hurdles first, then moved capital. Pattern: geopolitical clearance
before strategic investment. Signals Middle East as next AI infrastructure theatre.
History: Jul 18 — MS lobbied Commerce on UAE export controls. Now clear why.
Prediction: Saudi PIF responds with competing Gulf AI deal within 60 days.
Entities: Microsoft · G42 · UAE · US Commerce Dept · Huawei

---

🔬 TECHNOLOGY · #2
Meta releases Llama 3.1 405B open-weights model
https://ai.meta.com/blog/meta-llama-3-1

Largest open model to date. Matches GPT-4 on most benchmarks. Meta's
commoditization play — zero cost removes OpenAI's pricing leverage.
History: 4th Llama release in 8 months. Gap to GPT-4 closing ~15% per release.
Prediction: OpenAI capability response within 3 weeks. They always counter.
Entities: Meta · Llama 3.1 · OpenAI · GPT-4 · Hugging Face

---

⚡ POWER · #3
EU fines Apple €1.8B under Digital Markets Act
https://ec.europa.eu/commission/presscorner/...

First DMA fine. App Store music streaming restriction ruled illegal.
Entities: Apple · European Union · Digital Markets Act · Spotify

---

🏗️ INFRASTRUCTURE · #4
TSMC breaks ground on Arizona fab 2
https://techcrunch.com/2026/07/25/tsmc-arizona-fab-2

CHIPS Act investment materialising. Fab 1 delays absorbed. Schedule: 2028 volume.
History: Jul 10 — TSMC CFO flagged Arizona cost 50% above Taiwan equivalent.
Prediction: Intel lobbies for additional CHIPS Act tranche before Q4.
Entities: TSMC · Arizona · CHIPS Act · Intel · Taiwan · Nvidia · Apple

---

👥 TALENT · #5
OpenAI safety researcher moves to Anthropic
https://theverge.com/2026/07/25/openai-anthropic-researcher

4th departure in 3 months. All safety-focused roles. Structural, not coincidental.
Prediction: OpenAI announces revised safety commitments within 30 days — PR response.
Entities: OpenAI · Anthropic · AI Safety

---

GIANT WATCH
🍎 Apple — No major news. EU fine (Signal #3). Stock -0.8%.
🔵 Meta — Llama 3.1 (Signal #2). Reality Labs hiring freeze lifted.
🟢 Nvidia — 3 chip design patents filed. H100 supply still constrained.
🔴 Google — DeepMind protein folding v2 paper. Quiet but high-signal.
Ⓜ️ Microsoft — UAE deal (Signal #1). Azure SEA outage, 40min.
🟠 Amazon — AWS GPU instance price cuts. Response to Google TPU pricing.
🔵 OpenAI — Safety researcher departure (Signal #5). No comment.
🇨🇳 Baidu — ERNIE Bot crossed 200M users in China.

---

If models are free and compute is commoditising — what stays scarce?

---
94 ingested · 8 surfaced · Ollama ✓ · Accuracy 7/11 (64%)
```

---

### Example: Beginner-Friendly Style

```
Tech Intel Briefing — Friday, 25 Jul 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━

TODAY'S PICTURE
8 signals · 2 history callbacks · 1 prediction confirmed · 2 new predictions

━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEFORE YOU READ — WHAT WE CALLED

✅ CONFIRMED (Jul 22)
We said: Anthropic's unusual infra hiring pattern suggests a major compute
deal is imminent — likely with one of the big cloud providers.
Today: Anthropic announced a 3x compute expansion deal with Google Cloud.
This is what confirmation looks like — when a company hires infra engineers
before announcing a deal, it usually means the deal was already in progress.
Talent movement is one of the earliest signals available to us.

⏳ STILL WATCHING (Jul 20)
We said: The EU's informal comments about Nvidia's AI chip dominance
will likely turn into a formal investigation within 45 days.
Today: No update. 5 days elapsed. Still watching.
We're keeping this flagged because EU regulatory moves tend to be slow
to announce but fast to act once announced.

Running prediction accuracy: 7/11 (64%) since Jul 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 CAPITAL · Signal #1
Microsoft invests $1.5B in UAE AI firm G42
https://reuters.com/technology/microsoft-g42-investment

What this means:
Microsoft (the company behind Windows, Xbox, and a major investor in
OpenAI) just put $1.5 billion into G42 — an AI company owned by the Abu
Dhabi government in the UAE. G42 is the Middle East's flagship attempt to
build national AI capability. This deal was complicated because G42
previously had ties to Huawei (a Chinese tech firm the US government
considers a security risk). Microsoft had to get US government clearance
before the investment was allowed to go through.

Why it matters to you:
This is a pattern you'll see repeatedly: big tech companies are not just
selling products globally, they're buying strategic positions in new
regions before those regions become major AI markets. The Gulf states
(UAE, Saudi Arabia, Qatar) have enormous oil wealth and are spending it
to become AI powers. When Microsoft pays $1.5B for influence in Abu
Dhabi, it's not about selling software — it's about who controls AI
infrastructure in the next decade.

Connected to history:
On Jul 18 we noted Microsoft quietly lobbying the US Commerce Department
on UAE technology export rules. At the time it seemed minor. Today makes
clear why — they were clearing the regulatory path for this investment
before announcing it. This is a 7-day setup-to-execution pattern.

What we predict next:
Saudi Arabia's Public Investment Fund (the sovereign wealth fund that
owns stakes in everything from Uber to Newcastle United) will announce a
competing Gulf AI infrastructure deal within 60 days. Gulf states are in
an AI arms race — when one moves, others follow quickly.

Entities: Microsoft · G42 · UAE · US Commerce Dept · Huawei · OpenAI

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 TECHNOLOGY · Signal #2
Meta releases Llama 3.1 405B — largest open AI model ever released
https://ai.meta.com/blog/meta-llama-3-1

What this means:
Meta (the company behind Facebook, Instagram, and WhatsApp) just released
a free, open-source AI model called Llama 3.1 405B. "Open source" means
anyone can download it and use it for free — including running it
locally on their own computer. The "405B" refers to 405 billion
parameters, which is a rough measure of the model's size and capability.
This model matches GPT-4 (OpenAI's flagship, which costs money to use)
on most standard tests.

Why it matters to you:
The model you're running locally right now — Llama 3.2 — is from this
same family. Meta is deliberately making powerful AI free because it
removes OpenAI's main advantage: charging money for intelligence.
If the best AI model is free, OpenAI can't build a business just on
"we have the best model." This forces every AI company to compete on
something other than model quality — data, distribution, trust,
integration. That shift is happening right now.

Connected to history:
This is Meta's 4th major Llama release in 8 months. Each release has
closed the quality gap with GPT-4 by approximately 15%. At this pace,
open models will match or exceed the best closed models by early 2027.

What we predict next:
OpenAI will announce a new GPT-4o capability expansion within 3 weeks.
This is a consistent pattern — every time Meta ships something
significant, OpenAI responds publicly within 21 days. Watch for it.

Entities: Meta · Llama 3.1 · OpenAI · GPT-4 · Hugging Face

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ POWER · Signal #3
EU fines Apple €1.8 billion for App Store anti-competition
https://ec.europa.eu/commission/presscorner/...

What this means:
The European Union (the governing body of 27 European countries) fined
Apple €1.8 billion — roughly $2 billion. The reason: Apple was blocking
music apps like Spotify from telling users they could subscribe more
cheaply directly on Spotify's website instead of through the App Store.
This is the first major fine under the Digital Markets Act (DMA) — a new
European law passed in 2022 specifically to limit how much control big
tech platforms have over their own ecosystems.

Why it matters to you:
Governments are now actively reshaping the rules of how digital platforms
work. This isn't just about Apple and Spotify — it sets a precedent.
The EU passed DMA, the US is running multiple antitrust cases against
Google and Amazon, and India is watching all of this closely.
Regulatory pressure on Big Tech is not a one-off event — it's a
structural shift that will play out over the next 5-10 years.

What we predict next:
Apple will appeal and simultaneously make a minor App Store policy
change to demonstrate compliance — their standard playbook to slow
enforcement while the legal process runs.

Entities: Apple · European Union · Digital Markets Act · Spotify

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️ INFRASTRUCTURE · Signal #4
TSMC begins construction of second Arizona chip factory
https://techcrunch.com/2026/07/25/tsmc-arizona-fab-2

What this means:
TSMC (Taiwan Semiconductor Manufacturing Company) is the factory that
makes chips for Apple, Nvidia, AMD, and almost every other major tech
company. They don't design chips — they just manufacture them, and they
do it better than anyone else. TSMC is based in Taiwan. Their second US
factory in Arizona just broke ground. This is funded in part by the CHIPS
Act — a $52 billion US government program to bring chip manufacturing
back to America.

Why it matters to you:
Right now, about 90% of the world's most advanced chips are made in
Taiwan. If China ever moved against Taiwan militarily, the entire global
tech industry would freeze — no chips means no iPhones, no AI servers,
no data centres. The US is spending billions to reduce this single point
of failure. Every AI product you use depends on chips. This factory is
part of the answer to "what happens if the supply breaks?"

Connected to history:
On Jul 10 TSMC's CFO noted that building in Arizona costs 50% more than
building in Taiwan. The US is essentially paying a premium to reduce
geopolitical risk. That cost context makes the CHIPS Act investment
make more sense — it's not a subsidy, it's insurance.

What we predict next:
Intel will lobby for an additional CHIPS Act funding tranche before
Q4 2026, using TSMC's progress as evidence the program is working.

Entities: TSMC · Arizona · CHIPS Act · Apple · Nvidia · Intel · Taiwan · China

━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 TALENT · Signal #5
Senior OpenAI safety researcher leaves for Anthropic
https://theverge.com/2026/07/25/openai-anthropic-researcher

What this means:
A senior researcher focused on AI safety at OpenAI has left and joined
Anthropic. Anthropic was founded in 2021 by former OpenAI employees
who left over disagreements about how fast to move and how seriously to
take safety risks. This is the 4th such departure from OpenAI to a
safety-focused competitor in the last 3 months.

Why it matters to you:
When people leave a company — especially to go to a direct competitor —
it tells you something about internal priorities and culture that no
press release will. Safety researchers leaving OpenAI specifically for
Anthropic (which was built on safety as a core principle) suggests a
culture gap is widening. This is a talent signal, not a technology signal.
Over time, where the best people go is where the real work happens.

What we predict next:
OpenAI will publish a public statement on their safety commitments within
30 days. This is their standard PR response to talent departure stories.

Entities: OpenAI · Anthropic · AI Safety

━━━━━━━━━━━━━━━━━━━━━━━━━━━

GIANT WATCH
Companies we always monitor. Brief update even on quiet days.

🍎 Apple (makes iPhone, Mac, and runs the App Store)
EU fine today (Signal #3). Stock down 0.8%. Appeal expected.

🔵 Meta (makes Facebook, Instagram, WhatsApp)
Llama 3.1 release today (Signal #2). Also: hiring freeze lifted in Reality
Labs — their VR/AR division. Signals renewed investment in spatial computing.

🟢 Nvidia (makes the GPUs that power AI training and inference)
No major news. Filed 3 new chip design patents quietly. H100 GPU supply
still constrained — demand continues to outpace production.

🔴 Google (search, YouTube, Android, Google Cloud, DeepMind)
DeepMind published a research paper on protein folding version 2.
Quiet news day but scientifically significant — protein folding affects
drug discovery. Low noise, high long-term signal.

Ⓜ️ Microsoft (Windows, Azure cloud, GitHub, invested in OpenAI)
UAE deal today (Signal #1). Also: Azure (their cloud platform) had a
40-minute outage in Southeast Asia — minor but worth noting.

🟠 Amazon (AWS cloud, e-commerce, Alexa, Anthropic investor)
AWS quietly cut prices on GPU computing instances. Likely a direct
response to Google lowering TPU (their custom chip) pricing.
Cloud price wars benefit developers — cheaper AI compute.

🔵 OpenAI (makes ChatGPT and GPT-4)
Safety researcher departure today (Signal #5). No public comment yet.

🇨🇳 Baidu (China's Google — search + AI)
ERNIE Bot (their ChatGPT equivalent) crossed 200 million users in China.
Chinese AI is scaling fast inside China, even if invisible outside it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

ONE QUESTION WORTH SITTING WITH
If AI models are becoming free (Llama), compute is getting cheaper
(AWS price cuts), and safety researchers are leaving OpenAI — what
is actually scarce in AI right now? Data? Trust? Distribution?
The answer to that question is where the real power is shifting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
94 signals ingested · 8 surfaced · Ollama ✓
Prediction accuracy this week: 7/11 (64%)
```

---

## Notes on Telegram Formatting

- **No images** — Telegram supports images but briefings are text-only by design. Images break the "readable in 60 seconds" principle and don't render well in notification previews.
- **No tables** — Telegram does not render markdown tables. Use plain text lists or dashes instead.
- **Bold** — Use `*text*` for bold in Telegram (not `**text**`). The system formats output for Telegram's MarkdownV2 parser before sending.
- **Links** — Use plain URLs on their own line. Telegram auto-previews the first link in a message. For subsequent links, plain URL is cleanest.
- **Emoji** — Renders natively on all platforms. Used for domain tags, company icons, status markers. No images needed.
- **Length** — Beginner-friendly briefing is intentionally long (~1,200 words). Telegram has a 4,096 character limit per message. The system splits into multiple messages if needed, with a clear continuation marker.
- **Character limit handling** — If briefing exceeds 4,096 chars, split at `━━━` section breaks. Never split mid-signal.
