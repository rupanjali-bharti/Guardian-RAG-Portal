# --- Updated Automation Loop in app.py ---
if st.button("🚀 Start Audit", type="primary"):
    with st.status("Analyzing documentation...", expanded=True) as status:
        temp_results = []
        for i, q in enumerate(questions):
            res = run_rag_single(q)
            ans_text = res.get('Answer', '').lower()
            cit_text = str(res.get('Citation', '')).lower()

            # STRICTER LOGIC: Flag as Low if any of these conditions are met
            is_gap = any(phrase in ans_text for phrase in [
                "not specified", "not mentioned", "does not specify", 
                "no information", "not found", "unavailable", "don't know"
            ])
            has_no_citation = cit_text in ["n/a", "none", "", "unknown", "nan"]
            
            # If the answer is very short (e.g., under 30 chars), it's likely a failure
            is_too_short = len(ans_text) < 30 

            if is_gap or has_no_citation or is_too_short:
                res['Confidence'] = "Low"
            else:
                res['Confidence'] = "High"
                
            temp_results.append(res)
        st.session_state.rag_results = temp_results
        status.update(label="✅ Analysis Complete", state="complete")