
import argparse, asyncio, json, datetime
from agents import run_all_agents
from rag_stubs import RAGClient

async def main(lc_file, mapping_file):
    with open(lc_file, 'r', encoding='utf-8') as f:
        lc_text = f.read()
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    rag = RAGClient()
    findings = await run_all_agents(lc_text, mapping, rag)
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    with open(f'report_{ts}.json', 'w', encoding='utf-8') as f:
        json.dump(findings, f, indent=2)
    with open(f'report_{ts}_human.md', 'w', encoding='utf-8') as f:
        f.write('# LC Validation Report\\n\\n')
        for agent in findings['agents']:
            f.write(f"## {agent['agent_name']}\\n")
            f.write(f"Status: {agent['status']}\\n\\n")
            for item in agent['checks']:
                f.write(f"- {item['check']}: {item['result']}\\n")
            f.write('\\n')
    print('Reports generated:', f'report_{ts}.json', f'report_{ts}_human.md')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lc-file', default='sampleLC.txt')
    parser.add_argument('--mapping-file', default='mapping.json')
    args = parser.parse_args()
    asyncio.run(main(args.lc_file, args.mapping_file))
