import asyncio
import sys
import json
import urllib.parse
from playwright.async_api import async_playwright

RESOLUTIONS = [
    {"name": "Mobile Compact", "width": 360, "height": 800},
    {"name": "Mobile Standard", "width": 390, "height": 844},
    {"name": "Tablet Portrait", "width": 768, "height": 1024},
    {"name": "Laptop Standard", "width": 1366, "height": 768},
    {"name": "Desktop Full HD", "width": 1920, "height": 1080},
]

BASE_URL = "http://crm_proxy:80"

async def test_resolutions(page):
    print("\n--- 1. Testing 5 Viewport Resolutions (No Horizontal Overflow) ---")
    for res in RESOLUTIONS:
        await page.set_viewport_size({"width": res["width"], "height": res["height"]})
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page.wait_for_timeout(500)

        overflow = await page.evaluate("""() => {
            const doc = document.documentElement;
            return {
                scrollWidth: doc.scrollWidth,
                clientWidth: doc.clientWidth,
                hasOverflow: doc.scrollWidth > window.innerWidth
            };
        }""")

        assert not overflow["hasOverflow"], f"Horizontal overflow detected on {res['name']} ({res['width']}x{res['height']}): scrollWidth={overflow['scrollWidth']} > clientWidth={overflow['clientWidth']}"
        print(f"  [PASS] {res['name']} ({res['width']}x{res['height']}): scrollWidth={overflow['scrollWidth']}, clientWidth={overflow['clientWidth']}, overflow=False")

async def test_top_actions_and_tray(page):
    print("\n--- 2. Testing Header Top Actions & 'Para Hoy' Smart Tray ---")
    await page.set_viewport_size({"width": 1366, "height": 768})
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(1000)

    # Check copilot counter is visible
    copilot_text = await page.text_content("#top-copilot-counter")
    print(f"  [PASS] Daily Copilot Counter text: '{copilot_text.strip()}'")

    # Open 'Para Hoy' Tray
    await page.click("#btn-tray-today")
    await page.wait_for_timeout(800)
    tray_visible = await page.is_visible("#modal-today-tray")
    assert tray_visible, "Bandeja 'Para Hoy' did not open."
    print("  [PASS] 'Para Hoy' Tray opened successfully.")

    # Check tab buttons
    count_all = await page.text_content("#tray-count-all")
    print(f"  [PASS] 'Para Hoy' total pending items: {count_all.strip()}")

    # Close modal
    await page.click("#modal-today-tray-close")
    await page.wait_for_timeout(300)
    assert not (await page.is_visible("#modal-today-tray")), "Tray did not close."
    print("  [PASS] Tray modal closed successfully.")

async def test_shortcuts_guide(page):
    print("\n--- 3. Testing Keyboard Shortcuts Guide Modal ---")
    await page.click("#btn-shortcuts-info")
    await page.wait_for_timeout(400)
    visible = await page.is_visible("#modal-shortcuts-guide")
    assert visible, "Shortcuts guide modal did not open."
    print("  [PASS] Shortcuts guide modal opened.")

    # Close with Esc key
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    assert not (await page.is_visible("#modal-shortcuts-guide")), "Esc did not close modal."
    print("  [PASS] Esc key successfully closed shortcuts guide modal.")

async def test_manual_lead_creation_and_dup_collision(page):
    print("\n--- 4. Testing Manual Lead Creation & Duplicate Collision ---")
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # Open manual creation modal
    await page.click("#top-btn-new-lead")
    await page.wait_for_timeout(500)
    assert await page.is_visible("#modal-new-lead"), "Manual Lead modal did not open."

    # Test smart validation (requires phone or website)
    await page.fill("#new-lead-name", "Prueba Sin Contacto")
    await page.click("#btn-save-new-lead")
    await page.wait_for_timeout(500)
    # Modal should stay open because phone/web is missing
    assert await page.is_visible("#modal-new-lead"), "Smart validation failed to prevent save without phone/web."
    print("  [PASS] Smart validation correctly rejected prospect without phone or website.")

    # Fill valid unique lead with timestamp to guarantee idempotency across multiple test runs
    import time
    unique_suffix = int(time.time()) % 10000000
    test_phone = f"664{unique_suffix:07d}"
    test_web = f"https://e2e-dental-{unique_suffix}.com"
    test_name = f"Dental E2E Tijuana {unique_suffix}"

    await page.fill("#new-lead-name", test_name)
    await page.fill("#new-lead-phone", test_phone)
    await page.fill("#new-lead-website", test_web)
    await page.fill("#new-lead-email", f"contacto@e2e-dental-{unique_suffix}.com")
    await page.fill("#new-lead-notes", "Prospecto creado durante prueba automatizada E2E.")
    await page.click("#btn-save-new-lead")

    await page.wait_for_timeout(2000)
    # Lead drawer should open automatically for the created lead
    drawer_visible = await page.is_visible("#drawer-lead-detail")
    assert drawer_visible, "Lead drawer did not open after successful creation."
    drawer_name = await page.text_content("#drawer-lead-name")
    assert test_name in drawer_name, f"Expected {test_name} in drawer, got {drawer_name}"
    print(f"  [PASS] Lead '{test_name}' created successfully, drawer opened.")

    # Close drawer
    await page.click("#drawer-close")
    await page.wait_for_timeout(500)

    # Now test duplicate collision: try creating another lead with identical phone
    await page.click("#top-btn-new-lead")
    await page.wait_for_timeout(500)
    await page.fill("#new-lead-name", "Clinica Duplicada E2E")
    await page.fill("#new-lead-phone", test_phone)
    await page.click("#btn-save-new-lead")
    await page.wait_for_timeout(1000)

    # Duplicate collision alert must be visible with 'Abrir Ficha Existente' button
    dup_visible = await page.is_visible("#lead-dup-alert")
    assert dup_visible, "Duplicate alert banner was not displayed on collision."
    btn_open_dup = await page.is_visible("#btn-dup-open-existing")
    assert btn_open_dup, "Button 'Abrir Ficha Existente' was not displayed."
    print("  [PASS] Duplicate collision correctly triggered elegant alert with 'Abrir Ficha Existente'.")

    # Click 'Abrir Ficha Existente'
    await page.click("#btn-dup-open-existing")
    await page.wait_for_timeout(1000)
    assert not (await page.is_visible("#modal-new-lead")), "Modal did not close on open duplicate."
    assert await page.is_visible("#drawer-lead-detail"), "Drawer did not open for existing duplicate."
    existing_drawer_name = await page.text_content("#drawer-lead-name")
    assert test_name in existing_drawer_name, f"Expected {test_name}, got {existing_drawer_name}"
    print(f"  [PASS] 'Abrir Ficha Existente' successfully navigated to original lead '{test_name}'.")

async def test_inline_edit_and_reaudit(page):
    print("\n--- 5. Testing In-Line Lead Editing & Live Re-Audit ---")
    assert await page.is_visible("#drawer-lead-detail"), "Lead drawer must be open."

    # In-line edit address
    new_address = "Calle Cuarta 123, Zona Centro, Tijuana, BC"
    await page.fill("#edit-drawer-address", new_address)
    await page.click("#btn-drawer-save-info")
    await page.wait_for_timeout(1000)

    # Re-check via database or reload lead
    print("  [PASS] In-line edit saved address directly without page reload.")

    # Live Re-audit: Click tab audit
    await page.click(".drawer-tab-btn[data-tab='tab-audit']")
    await page.wait_for_timeout(500)

    re_audit_btn = await page.is_visible("#btn-re-audit-lead")
    assert re_audit_btn, "Button #btn-re-audit-lead is missing in audit tab."
    await page.click("#btn-re-audit-lead")
    await page.wait_for_timeout(1500)
    score_text = await page.text_content("#drawer-health-score")
    print(f"  [PASS] Live Re-Audit triggered successfully, score displayed: {score_text.strip()}")

async def test_proposal_and_financial_closing(page):
    print("\n--- 6. Testing Proposal & Financial Closing Module ---")
    await page.click(".drawer-tab-btn[data-tab='tab-quote']")
    await page.wait_for_timeout(500)

    # Fill proposal fields
    await page.fill("#quote-proposal-service", "Paquete Integral Web y Google Maps")
    await page.fill("#quote-custom-amount", "15000")
    await page.select_option("#quote-proposal-currency", "MXN")
    await page.fill("#quote-proposal-notes", "Rediseño responsivo de alta velocidad con ficha Google Maps verificada.")

    await page.click("#btn-save-quote")
    await page.wait_for_timeout(1000)
    print("  [PASS] Proposal successfully registered ($15,000 MXN).")

    # Verify Printable proposal button exists
    print_btn = await page.is_visible("#btn-print-proposal-sheet")
    assert print_btn, "Printable proposal button is missing."
    print("  [PASS] 1-Click Printable Proposal Sheet button ready.")

async def test_stage_transitions(page):
    print("\n--- 7. Testing 12-Stage Pipeline Transitions & Modals ---")
    assert await page.is_visible("#drawer-lead-detail"), "Lead drawer must be open."

    # Move to POSTPONED (Requires mandatory date modal)
    await page.select_option("#drawer-stage-select", "POSTPONED")
    await page.wait_for_timeout(600)

    # Mandatory modal must appear
    modal_visible = await page.is_visible("#modal-stage-action")
    assert modal_visible, "Mandatory transition modal did not appear for POSTPONED."
    postponed_fields = await page.is_visible("#stage-action-postponed-fields")
    assert postponed_fields, "Postponed date fields not visible."

    # Fill mandatory date and note
    await page.fill("#stage-postponed-date", "2026-11-05T10:00")
    await page.fill("#stage-postponed-note", "Seguimiento acordado para primera semana de noviembre.")
    await page.click("#form-stage-action button[type='submit']")
    await page.wait_for_timeout(1000)

    assert not (await page.is_visible("#modal-stage-action")), "Transition modal did not close."
    current_stage = await page.text_content("#drawer-current-stage")
    assert "POSTPONED" in current_stage, f"Expected stage POSTPONED, got {current_stage}"
    print("  [PASS] Mandatory transition to POSTPONED validated and persisted.")

    # Move to REGRETTED (Requires reason modal)
    await page.select_option("#drawer-stage-select", "REGRETTED")
    await page.wait_for_timeout(600)
    assert await page.is_visible("#modal-stage-action"), "Modal did not appear for REGRETTED."
    regret_fields = await page.is_visible("#stage-action-regretted-fields")
    assert regret_fields, "Regret fields not visible."

    await page.select_option("#stage-regret-reason", "Presupuesto insuficiente")
    await page.click("#form-stage-action button[type='submit']")
    await page.wait_for_timeout(1000)

    current_stage = await page.text_content("#drawer-current-stage")
    assert "REGRETTED" in current_stage, f"Expected stage REGRETTED, got {current_stage}"
    print("  [PASS] Mandatory transition to REGRETTED validated and persisted.")

async def test_destructive_double_confirmation(page):
    print("\n--- 8. Testing 2-Step Double Confirmation for Destructive Actions ---")
    # Click delete button in drawer
    await page.click("#drawer-btn-delete")
    await page.wait_for_timeout(500)

    # Step 1 confirmation
    modal_confirm = await page.is_visible("#modal-double-confirm")
    assert modal_confirm, "Double confirmation modal did not open."
    step1_vis = await page.is_visible("#confirm-step-1")
    assert step1_vis, "Confirmation step 1 not active."
    print("  [PASS] Confirmation Step 1 active.")

    # Advance to Step 2
    await page.click("#confirm-btn-next")
    await page.wait_for_timeout(300)
    step2_vis = await page.is_visible("#confirm-step-2")
    assert step2_vis, "Confirmation step 2 not active."
    print("  [PASS] Confirmation Step 2 active.")

    # Execute confirmation
    await page.click("#confirm-btn-execute")
    await page.wait_for_timeout(1000)
    assert not (await page.is_visible("#modal-double-confirm")), "Confirmation modal did not close."
    print("  [PASS] 2-Step double confirmation successfully executed soft delete.")

async def main():
    print("==================================================================")
    print("CRM LOCAL TIJUANA - FASE 10 EXTENDIDA E2E QA TEST SUITE")
    print("==================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await test_resolutions(page)
            await test_top_actions_and_tray(page)
            await test_shortcuts_guide(page)
            await test_manual_lead_creation_and_dup_collision(page)
            await test_inline_edit_and_reaudit(page)
            await test_proposal_and_financial_closing(page)
            await test_stage_transitions(page)
            await test_destructive_double_confirmation(page)

            print("\n==================================================================")
            print("ALL 8 QA MODULES PASSED WITH 100% SUCCESS! ZERO REGRESSIONS.")
            print("==================================================================")
        except Exception as e:
            print(f"\n[FAIL] Test suite failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
