# X Thread Draft

1/ I asked five LLMs to write 1,000 short story openings.

Then I counted the character names.

The result: in 763/1,000 stories, the model reached for a name from a small,
predictable overused pool.

Everyone's name is Elara now.

2/ The champion was Elara.

It appeared in 153/1,000 story openings.

But the model split is the interesting part:

- Gemini: 46%
- DeepSeek: 19%
- GPT-5-mini: 6%
- Llama: 4%
- Claude: 2%

Each model has an accent.

3/ This is not just "models use common names."

I compared model frequency with human baselines:

- SSA baby-name data for first names
- US Census surname data for surnames

Elara is roughly 48,800x overrepresented against its US baby-name baseline.

4/ Gemini's female-name distribution is especially collapsed.

Among Gemini's female first-name mentions, Elara alone accounts for 46%.

Other models collapse onto different names: Llama/GPT like Emily, Claude leans
hard on Marcus, and DeepSeek likes Leo/Arthur/Clara.

5/ The role split was also skewed.

The prompt asked for a protagonist and one secondary character.

Pooled across all models:

- protagonists: 76% female
- secondary characters: 35% female

Most common template: female lead + male secondary.

6/ This part needs caution.

The prompt may be shaping the result. "Protagonist plus secondary character" can
nudge familiar patterns: heroine + colleague, detective, assistant, brother,
mentor, etc.

But the skew is large enough to deserve a proper control run.

7/ This connects to prior work.

Brzozowski & Chung's "The Ghost Couple" paper found that LLMs repeat correlated
name clusters: Marcus Chen, Elena Vasquez, Aris Thorne, Elara Voss.

My data is a fiction-domain version of that phenomenon.

8/ The overlap is neat.

Their Claude fingerprints, Marcus Chen and Elena Vasquez, show up only in my
Claude samples too.

But their GPT-associated "Elara Voss" never appears. In fiction, bare Elara is
mostly Gemini's habit.

The fingerprint moves by domain/version.

9/ Practical output: a blocklist.

Most overused real first names:

Elara, Eira, Kaelen, Thorne, Hawk, Kael, Lyra, Arin, Emilia, Lena, Leo, Maya,
Clara, Marcus, Elias, Arthur, Liam.

Surnames:

Blackwood, Windsor, Mayfield, Thorne, Chen, Patel.

10/ Caveats:

- five models
- one prompt shape
- 200 samples/model
- completions capped at 80 tokens
- NER extraction has long-tail noise

So I trust the broad pattern much more than the exact rank of name #37.

11/ Why care?

Names are a tiny decision. No deep reasoning required.

That makes them a clean window into a model's default distribution of "what a
story character sounds like."

And that distribution is much narrower than it looks.

12/ The point is not that Elara is a bad name.

It is that she should not be every name.

Repo has raw samples, counts, report, blocklist, and visuals:

[ADD GITHUB URL]
