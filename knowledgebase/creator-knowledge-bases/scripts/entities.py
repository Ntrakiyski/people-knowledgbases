"""Index a disclosed list of named mentions without inventing biographies."""
import hashlib
import re
from collections import defaultdict

REGISTRY = {
    'people': ['Alex Hormozi', 'Codie Sanchez', 'Dan Martell', 'Nick Huber', 'Sahil Bloom',
               'Sharran Srivatsaa', 'Warren Buffett', 'Charlie Munger', 'Jeff Bezos',
               'Elon Musk', 'Sam Altman', 'Steve Jobs', 'Mark Zuckerberg',
               'Naval Ravikant', 'Simon Sinek', 'Peter Thiel', 'Paul Graham',
               'Leila Hormozi', 'Wayne Huizenga', 'Richard Branson', 'Adam Grant',
               'Tim Ferriss', 'Peter Drucker', 'Neville Goddard', 'Jim Murphy',
               'Dan Hagberg', 'Mitchell Baldridge', 'Valter Longo'],
    'organizations': ['Goldman Sachs', 'Berkshire Hathaway', 'Acquisition.com',
                      'Contrarian Thinking', 'OpenAI', 'Anthropic', 'Microsoft',
                      'Google', 'Amazon', 'YouTube', 'LinkedIn', 'Instagram', 'TikTok',
                      'Somewhere.com', 'Bolt Storage', 'Storage Squad', 'Martell Ventures'],
    'tools': ['ChatGPT', 'Claude', 'Gemini', 'NotebookLM', 'Perplexity', 'HubSpot',
              'Salesforce', 'Zapier', 'GoHighLevel', 'n8n', 'Cursor', 'Grok',
              'Obsidian', 'Notion', 'Slack', 'Gmail', 'Gamma', 'Gumloop', 'Apex'],
    'books': ['The Sweaty Startup', 'The Five Types of Wealth', 'Buy Back Your Time',
              'The Goal', 'The Effective Executive', 'Feeling is the Secret',
              'Inner Excellence', 'Main Street Millionaire', '$100M Offers',
              '$100M Leads', '$100M Money Models'],
}


def build_entities(folder, config, imported, videos, write_page, transcript):
    by_video, records, groups = defaultdict(list), [], defaultdict(list)
    for kind, names in REGISTRY.items():
        for name in names:
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            matches = []
            pattern = re.compile(r'(?<!\w)' + re.escape(name) + r'(?!\w)', re.I)
            for key, provenance in imported.items():
                text = transcript(folder, key)
                match = pattern.search(text)
                if not match:
                    continue
                # The exact surrounding passage lets readers inspect identity and usage.
                before = list(re.finditer(r'\S+', text[:match.start()]))
                after = list(re.finditer(r'\S+', text[match.end():]))
                start = before[-12].start() if len(before) >= 12 else 0
                end = match.end() + after[11].end() if len(after) >= 12 else len(text)
                quote = text[start:end]
                record = {'creator_slug': config['slug'], 'entity': name, 'entity_kind': kind,
                          'entity_slug': slug, 'youtube_id': key, 'video_url': videos[key]['url'],
                          'quote': quote, 'character_start': start, 'character_end': end,
                          'matched_name': text[match.start():match.end()],
                          'name_start': match.start(), 'name_end': match.end(),
                          'raw_sha256': provenance['sha256'],
                          'method': 'literal first mention per video from disclosed registry',
                          'review_status': 'name mention; identity and endorsement not inferred'}
                records.append(record)
                matches.append(record)
                by_video[key].append((name, f'../entities/{kind}/{slug}.md'))
            if not matches:
                continue
            body = [f'# {name}', '',
                    'This page indexes literal name mentions in the saved transcripts. A mention does not establish identity, affiliation, endorsement, a recommendation, or the truth of a claim. Names such as Claude, Cursor, Apex, or The Goal need context to disambiguate. Only the first matching passage per video is shown.', '']
            for record in matches:
                key = record['youtube_id']
                body += [f"## {videos[key]['title']}", '', f"> {record['quote']}", '',
                         f"[Raw transcript](../../raw/{key}.md), characters {record['character_start']}–{record['character_end']} (end exclusive); [video]({record['video_url']}).", '']
            write_page(folder / 'entities' / kind / f'{slug}.md', 'entity', name, '\n'.join(body), entity_kind=kind, evidence_status='literal mentions; contextual interpretation required')
            groups[kind].append(f'- [{name}]({slug}.md): {len(matches)} source passage(s).')
    for kind in REGISTRY:
        write_page(folder / 'entities' / kind / 'index.md', 'overview', kind.capitalize(),
                   f'# {kind.capitalize()}\n\n' + '\n'.join(groups[kind] or ['No registered names found yet.']))
    scope = '; '.join(f"{kind}: {', '.join(names)}" for kind, names in REGISTRY.items())
    write_page(folder / 'entities/index.md', 'overview', 'Named mentions',
               '# Named mentions\n\nThis is a curated name index, not an exhaustive named-entity extraction or a biography database. Captions can misspell or omit names. Names are matched literally; interpretations and endorsements are not inferred.\n\n'
               '- [Contextual reading guide](review.md).\n- [People](people/index.md).\n- [Organizations](organizations/index.md).\n- [Tools](tools/index.md).\n- [Books](books/index.md).\n\n## Disclosed search registry\n\n' + scope)
    return by_video, records
