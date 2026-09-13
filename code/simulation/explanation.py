def generate_explanation(
    request,
    profile,
    status,
    method,
    plan,
    earliest_date,
    spending_changes,
    amount_safe,
    data_loader
):
    curr = profile['home_currency']
    min_bal = float(profile['minimum_balance_to_keep'])
    min_bal_str = f"{min_bal:,.2f}".rstrip('0').rstrip('.') if min_bal != int(min_bal) else f"{int(min_bal):,}"
    req_amt = float(request['requested_amount'])
    req_amt_str = f"{req_amt:,.2f}".rstrip('0').rstrip('.') if req_amt != int(req_amt) else f"{int(req_amt):,}"
    
    if status == 'affordable_now' and method == 'full_payment':
        return f"Pay {curr} {req_amt_str} today. This leaves at least {curr} {min_bal_str} available over the next 90 days."

    elif status == 'affordable_with_plan':
        if method == 'installments':
            # Extract installment details from plan
            payments = plan.split('|')
            count = len(payments)
            first_date, first_amt = payments[0].split(':')
            amt_num = float(first_amt)
            amt_str = f"{amt_num:,.2f}".rstrip('0').rstrip('.') if amt_num != int(amt_num) else f"{int(amt_num):,}"
            
            # Format first_date as e.g. "8 August 2025" or "YYYY-MM-DD"
            try:
                from datetime import datetime
                d_obj = datetime.strptime(first_date, '%Y-%m-%d').date()
                date_formatted = d_obj.strftime('%d %B %Y').lstrip('0')
            except Exception:
                date_formatted = first_date

            return f"Use {count} installments of {curr} {amt_str}, starting {date_formatted}. This leaves at least {curr} {min_bal_str} available."

        elif method == 'partial_payment':
            payments = plan.split('|')
            first_amt = float(payments[0].split(':')[1])
            second_date, second_amt = payments[1].split(':')
            second_amt_num = float(second_amt)
            
            first_str = f"{first_amt:,.2f}".rstrip('0').rstrip('.') if first_amt != int(first_amt) else f"{int(first_amt):,}"
            second_str = f"{second_amt_num:,.2f}".rstrip('0').rstrip('.') if second_amt_num != int(second_amt_num) else f"{int(second_amt_num):,}"
            
            try:
                from datetime import datetime
                d_obj = datetime.strptime(second_date, '%Y-%m-%d').date()
                date_formatted = d_obj.strftime('%d %B %Y').lstrip('0')
            except Exception:
                date_formatted = second_date

            return f"Pay {curr} {first_str} today and the remaining {curr} {second_str} on {date_formatted}. This protects the {curr} {min_bal_str} minimum throughout."

        elif method == 'full_payment' and spending_changes != 'none':
            actions = []
            for ch in spending_changes.split('|'):
                if ch.startswith('stop:'):
                    eid = ch.split(':')[1]
                    evt = data_loader.events_by_id.get(eid, {})
                    desc = evt.get('description', 'flexible expense').lower()
                    actions.append(f"Stop the {desc}")
                elif ch.startswith('reduce_to:'):
                    parts = ch.split(':')
                    eid, new_val = parts[1], float(parts[2])
                    evt = data_loader.events_by_id.get(eid, {})
                    desc = evt.get('description', 'flexible expense').lower()
                    new_val_str = f"{new_val:,.2f}".rstrip('0').rstrip('.') if new_val != int(new_val) else f"{int(new_val):,}"
                    actions.append(f"Reduce {desc} to {curr} {new_val_str}")
            action_text = " and ".join(actions)
            return f"{action_text}, then pay {curr} {req_amt_str} today. This leaves at least {curr} {min_bal_str} available."

    elif status == 'affordable_later' and method == 'wait':
        try:
            from datetime import datetime
            d_obj = datetime.strptime(earliest_date, '%Y-%m-%d').date()
            date_formatted = d_obj.strftime('%d %B %Y').lstrip('0')
        except Exception:
            date_formatted = earliest_date
        return f"Wait until {date_formatted}, then pay {curr} {req_amt_str} in full. Paying sooner would put the {curr} {min_bal_str} minimum at risk."

    elif status == 'not_affordable' or method == 'not_recommended':
        desired_date = request.get('desired_completion_date', '')
        try:
            from datetime import datetime
            d_obj = datetime.strptime(desired_date, '%Y-%m-%d').date()
            date_formatted = d_obj.strftime('%d %B %Y').lstrip('0')
        except Exception:
            date_formatted = desired_date
        return f"Do not make this payment by {date_formatted}. None of the available options keeps the {curr} {min_bal_str} minimum protected."

    return f"Recommendation: {method} with status {status}."
