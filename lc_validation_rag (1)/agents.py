
import asyncio, re
from datetime import datetime
from rag_stubs import RAGClient

def extract_field(lc_text, field_name):
    patterns = {
        'LC Number': r'LC Number:\\s*(.+)',
        'Date of Issue': r'Date of Issue:\\s*(.+)',
        'Amount': r'Amount:\\s*(.+)',
        'Expiry Date': r'Expiry Date:\\s*(.+)',
        'Expiry Place': r'Expiry Place:\\s*(.+)',
        'Incoterm': r'Incoterm:\\s*(.+)',
        'Latest Shipment Date': r'Latest Shipment Date:\\s*(.+)',
        'Port of Loading': r'Port of Loading:\\s*(.+)',
        'Port of Discharge': r'Port of Discharge:\\s*(.+)',
        'Goods': r'Goods:\\s*(.+)',
        'Insurance': r'Insurance policy/certificate(.+)',
        'Documents': r'Documents Required:\\s*(.+)',
    }
    pat = patterns.get(field_name)
    if not pat:
        return None
    m = re.search(pat, lc_text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None

async def check_amount_currency(lc_text, mapping, rag:RAGClient):
    amt = extract_field(lc_text, 'Amount')
    result = {'check': 'Credit Amount present and currency', 'value': amt, 'result': 'FAIL'}
    if not amt:
        result['result'] = 'MISSING'
        return result
    m = re.search(r'([A-Z]{3})\\s*([0-9,\\.]+)', amt)
    if m:
        curr = m.group(1)
        if curr == 'USD':
            result['result'] = 'PASS'
            result['notes'] = 'Currency is USD'
        else:
            result['result'] = 'WARN'
            result['notes'] = f'Currency is {curr}, expected USD per policy'
    else:
        result['result'] = 'WARN'
        result['notes'] = 'Could not parse amount format'
    return result

async def check_insurance_coverage(lc_text, mapping, rag:RAGClient):
    insurance_text = re.search(r'Insurance policy/certificate[^\\n]*,?\\s*(.+)', lc_text, re.IGNORECASE)
    result = {'check': 'Insurance coverage >=110% and "All Risks"', 'value': None, 'result': 'FAIL'}
    if not insurance_text:
        result['result'] = 'MISSING'
        return result
    text = insurance_text.group(0)
    result['value'] = text
    if '110%' in text or '110 %' in text:
        if re.search(r'All\\s*Risks', text, re.IGNORECASE):
            result['result'] = 'PASS'
        else:
            result['result'] = 'WARN'
            result['notes'] = '"110%" present but "All Risks" not found'
    else:
        result['result'] = 'FAIL'
        result['notes'] = '110% minimum not found'
    return result

async def check_incoterm_on_invoice(lc_text, mapping, rag:RAGClient):
    inc = extract_field(lc_text, 'Incoterm')
    result = {'check': 'Incoterm present and must appear on invoice', 'value': inc, 'result': 'FAIL'}
    if not inc:
        result['result'] = 'MISSING'
        return result
    result['result'] = 'PASS'
    result['notes'] = 'Incoterm present in LC; verify on invoice via RAG retriever if available'
    return result

async def check_bill_of_lading_consignment(lc_text, mapping, rag:RAGClient):
    docs_block = re.search(r'Full set of clean on board marine bills of lading,?\\s*(.+)', lc_text, re.IGNORECASE)
    result = {'check': 'Bill of Lading consigned to order and freight prepaid', 'value': None, 'result': 'FAIL'}
    if not docs_block:
        result['result'] = 'MISSING'
        return result
    text = docs_block.group(0)
    result['value'] = text
    if 'consigned to order' in text.lower() and 'freight prepaid' in lc_text.lower():
        result['result'] = 'PASS'
    else:
        result['result'] = 'WARN'
        result['notes'] = 'B/L or freight terms may not match exactly; manual review recommended'
    return result

async def check_dates_validity(lc_text, mapping, rag:RAGClient):
    exp = extract_field(lc_text, 'Expiry Date')
    ship = extract_field(lc_text, 'Latest Shipment Date')
    result = {'check': 'Expiry and Latest Shipment date validity', 'expiry': exp, 'latest_shipment': ship, 'result': 'FAIL'}
    if not exp:
        result['result'] = 'MISSING'
        return result
    try:
        exp_dt = datetime.strptime(exp.strip(), '%B %d, %Y')
        if ship:
            ship_dt = datetime.strptime(ship.strip(), '%B %d, %Y')
            if ship_dt <= exp_dt:
                result['result'] = 'PASS'
            else:
                result['result'] = 'FAIL'
                result['notes'] = 'Shipment date after expiry'
        else:
            result['result'] = 'WARN'
            result['notes'] = 'Latest shipment date missing'
    except Exception as e:
        result['result'] = 'WARN'
        result['notes'] = f'Could not parse dates: {e}'
    return result

async def run_all_agents(lc_text, mapping, rag:RAGClient):
    tasks = [
        check_amount_currency(lc_text, mapping, rag),
        check_insurance_coverage(lc_text, mapping, rag),
        check_incoterm_on_invoice(lc_text, mapping, rag),
        check_bill_of_lading_consignment(lc_text, mapping, rag),
        check_dates_validity(lc_text, mapping, rag),
    ]
    results = await asyncio.gather(*tasks)
    agents = []
    for r in results:
        agents.append({
            'agent_name': r['check'],
            'status': r.get('result','UNKNOWN'),
            'checks': [r]
        })
    return {'agents': agents, 'summary': {'total_checks': len(results)}}
