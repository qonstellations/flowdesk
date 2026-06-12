# Guide: Integrating Admin Validation into the Streamlit Frontend

Because the AI agent is configured with read-only access to the `app/` directory to protect frontend design integrity, you can apply these small, clean changes yourself. 

Here are the precise instructions and code changes needed to connect the new backend validation flow with the Streamlit dashboard.

---

## 1. Add Validation Badges to Ticket Table
File to modify: [app/components/ticket_table.py](file:///D:/flowdesk/app/components/ticket_table.py)

Add a visual badge representing whether a ticket is **Approved**, **Rejected**, or **Needs Review** inside the ticket cards list.

### Proposed Code Diff:
```diff
@@ -47,6 +47,15 @@
         status = t.get("status", "Open")
         target_at = t.get("target_resolution_at") or t.get("sla_deadline")
         overdue = _is_overdue(target_at, status)
+        
+        validation_badge = ""
+        if status == "Open":
+            val_status = t.get("admin_approved", 0)
+            if val_status == 1:
+                validation_badge = '<span style="color:#4CD97B;padding:2px 9px;border-radius:20px;font-size:0.7rem;font-weight:600;border:1px solid #4CD97B60;background:rgba(76,217,123,0.1);margin-right:4px;">✓ Approved</span>'
+            elif val_status == -1:
+                validation_badge = '<span style="color:#FF4D6D;padding:2px 9px;border-radius:20px;font-size:0.7rem;font-weight:600;border:1px solid #FF4D6D60;background:rgba(255,77,109,0.1);margin-right:4px;">✗ Rejected</span>'
+            else:
+                validation_badge = '<span style="color:#FFD700;padding:2px 9px;border-radius:20px;font-size:0.7rem;font-weight:600;border:1px solid #FFD70060;background:rgba(255,215,0,0.1);margin-right:4px;">⚡ Needs Review</span>'
+
         sc = _STATUS_COLOR.get(status, "#00E5FF")
         pc = _PRIORITY_COLOR.get(t.get("priority", "Low"), "#00E5FF")
         border = "#FF4D6D" if overdue else sc
@@ -75,6 +84,7 @@
                     <div>
                         <b style="color:#E8ECF5;font-size:0.95rem;">#{t['ticket_id']} {t['title']}</b><br>
                         <span style="color:#8A94B0;font-size:0.8rem;">{dept} · {date}</span><br>
                         {target_html}
                     </div>
                     <div style="display:flex;gap:8px;align-items:center;flex-shrink:0;margin-left:12px;">
+                        {validation_badge}
                         <span style="color:{pc};padding:2px 9px;border-radius:20px;
                               font-size:0.7rem;font-weight:600;border:1px solid {pc}60;">
                             {t.get('priority','')}</span>
```

---

## 2. Add Approve/Reject Buttons to Admin Controls
File to modify: [app/components/ticket_detail.py](file:///D:/flowdesk/app/components/ticket_detail.py)

Add the **✓ Check Mark (Approve & Send Email)** and **✗ Cross Mark (Reject)** options for open tickets.

### Proposed Code Diff:
```diff
@@ -228,6 +228,31 @@
 def _admin_controls(ticket: dict, tid: int, current_status: str) -> None:
+    # ── Ticket Validation Controls (Approve / Reject) ──
+    if current_status == "Open":
+        val_status = ticket.get("admin_approved", 0)
+        st.markdown(
+            '<div style="font-size:0.72rem;color:#FFD700;font-weight:700;'
+            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:14px;">'
+            "Ticket Routing Validation</div>",
+            unsafe_allow_html=True,
+        )
+        col_val_approve, col_val_reject, _ = st.columns([2, 2, 3])
+        
+        with col_val_approve:
+            if st.button("✓ Approve & Email Dept", key=f"btn_approve_val_{tid}", type="primary", use_container_width=True):
+                import backend.validation_workflow as vw
+                if vw.approve_ticket_by_admin(tid):
+                    st.success("Ticket approved and escalation email sent to department.")
+                    st.rerun()
+                else:
+                    st.error("Failed to approve ticket or send email.")
+                    
+        with col_val_reject:
+            # Display red/secondary styling button
+            if st.button("✗ Reject Ticket", key=f"btn_reject_val_{tid}", use_container_width=True):
+                import backend.validation_workflow as vw
+                if vw.reject_ticket_by_admin(tid):
+                    st.info("Ticket marked as rejected / validation failed.")
+                    st.rerun()
+        
+        st.markdown("---")
+
     st.markdown(
         '<div style="font-size:0.72rem;color:#7C4DFF;font-weight:700;'
         'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:14px;">'
         "Admin Controls</div>",
         unsafe_allow_html=True,
     )
```

---

## 3. Verify Local Mock Email Output
If you do not configure an SMTP host, emails will automatically save as styled HTML files inside:
`data/mock_emails/`

You can open these generated files in any web browser to preview what will be sent to the department or student.
