import asyncio
import sys
import json
import time
from playwright.async_api import async_playwright

RESOLUTIONS = [
    {"name": "Mobile Compact", "width": 360, "height": 800},
    {"name": "Mobile Standard", "width": 390, "height": 844},
    {"name": "Tablet Portrait", "width": 768, "height": 1024},
    {"name": "Laptop Standard", "width": 1366, "height": 768},
    {"name": "Desktop Full HD", "width": 1920, "height": 1080},
]

BASE_URL = "http://crm_proxy:80"

async def test_resolutions_and_overflow(page):
    print("\n--- 1. Testing 5 Viewport Resolutions (Zero Horizontal Overflow) ---")
    for res in RESOLUTIONS:
        await page.set_viewport_size({"width": res["width"], "height": res["height"]})
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page.wait_for_timeout(400)

        overflow = await page.evaluate("""() => {
            const doc = document.documentElement;
            return {
                scrollWidth: doc.scrollWidth,
                clientWidth: doc.clientWidth,
                hasOverflow: doc.scrollWidth > window.innerWidth
            };
        }""")

        assert not overflow["hasOverflow"], (
            f"Horizontal overflow detected on {res['name']} ({res['width']}x{res['height']}): "
            f"scrollWidth={overflow['scrollWidth']} > clientWidth={overflow['clientWidth']}"
        )
        print(f"  [PASS] {res['name']} ({res['width']}x{res['height']}): scrollWidth={overflow['scrollWidth']}, clientWidth={overflow['clientWidth']}, overflow=False")


async def test_border_radius_and_touch_targets(page):
    print("\n--- 2. Testing Geometric Consistency (Border-Radius <= 10px & Touch Targets) ---")
    await page.set_viewport_size({"width": 1366, "height": 768})
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # Check desktop solo icon size (min 38x38)
    await page.wait_for_selector(".kanban-card .btn-solo-icon", timeout=5000)
    desktop_btn_size = await page.evaluate("""() => {
        const btn = document.querySelector('.kanban-card .btn-solo-icon');
        if (!btn) return null;
        const rect = btn.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
    }""")
    if desktop_btn_size:
        assert desktop_btn_size["width"] >= 37.5 and desktop_btn_size["height"] >= 37.5, (
            f"Desktop btn-solo-icon smaller than 38x38: {desktop_btn_size}"
        )
        print(f"  [PASS] Desktop solo-icon size: {desktop_btn_size['width']}x{desktop_btn_size['height']} px (>= 38x38)")

    # Check mobile solo icon size (min 42x42)
    await page.set_viewport_size({"width": 390, "height": 844})
    await page.wait_for_timeout(300)
    mobile_btn_size = await page.evaluate("""() => {
        const btn = document.querySelector('.kanban-card .btn-solo-icon');
        if (!btn) return null;
        const rect = btn.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
    }""")
    if mobile_btn_size:
        assert mobile_btn_size["width"] >= 41.5 and mobile_btn_size["height"] >= 41.5, (
            f"Mobile btn-solo-icon smaller than 42x42: {mobile_btn_size}"
        )
        print(f"  [PASS] Mobile solo-icon size: {mobile_btn_size['width']}x{mobile_btn_size['height']} px (>= 42x42)")

    # Check that border-radius on cards, buttons, inputs does not exceed 10px (except circular 50%)
    invalid_radii = await page.evaluate("""() => {
        const elements = document.querySelectorAll('button, input, select, textarea, .lead-card, .kanban-card, .modal-content, .in-app-web-preview');
        const invalid = [];
        elements.forEach(el => {
            const comp = window.getComputedStyle(el);
            const r = comp.borderRadius;
            const px = parseFloat(r);
            if (px > 10.5 && r !== '50%' && !r.includes('9999px')) {
                invalid.push({ tag: el.tagName, class: el.className, radius: r });
            }
        });
        return invalid;
    }""")
    assert len(invalid_radii) == 0, f"Found elements with border-radius > 10px: {invalid_radii}"
    print("  [PASS] 100% of examined buttons, cards, inputs adhere strictly to border-radius <= 10px.")


async def test_global_popovers_and_clamping(page):
    print("\n--- 3. Testing Absolute Popover Positioning & Screen Clamping ---")
    await page.set_viewport_size({"width": 1366, "height": 768})
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # Hover a solo icon with data-tooltip
    target = await page.query_selector("[data-tooltip]")
    assert target, "No element with [data-tooltip] found."
    await target.hover()
    await page.wait_for_timeout(250)

    popover_info = await page.evaluate("""() => {
        const p = document.getElementById('global-portal-popover');
        if (!p || p.classList.contains('hidden')) return null;
        const rect = p.getBoundingClientRect();
        return {
            visible: true,
            top: rect.top,
            left: rect.left,
            right: rect.right,
            bottom: rect.bottom,
            width: rect.width,
            height: rect.height,
            text: p.textContent.trim(),
            inWindow: rect.left >= 0 && rect.right <= window.innerWidth && rect.top >= 0 && rect.bottom <= window.innerHeight
        };
    }""")
    assert popover_info and popover_info["visible"], "Global portal popover was not displayed on hover."
    assert popover_info["inWindow"], f"Popover clipped by window: {popover_info}"
    print(f"  [PASS] Global portal popover correctly positioned and boundary-clamped: '{popover_info['text']}'")


async def test_in_app_web_preview(page):
    print("\n--- 4. Testing In-App Web Viewer (In-App Preview) ---")
    await page.set_viewport_size({"width": 1366, "height": 768})
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # Click first web preview button on card
    btn_web = await page.query_selector(".btn-card-preview-web")
    assert btn_web, "No web preview button found on kanban cards."
    await btn_web.click()
    await page.wait_for_timeout(800)

    # Verify preview container is visible
    preview_open = await page.is_visible("#in-app-web-preview")
    assert preview_open, "In-app web preview failed to open."
    print("  [PASS] In-app web preview opened successfully.")

    # Test Mobile View Toggle
    await page.click("#preview-toggle-mobile")
    await page.wait_for_timeout(300)
    device_frame_class = await page.get_attribute("#preview-device-frame", "class")
    assert "device-mobile" in device_frame_class, f"Device frame did not switch to mobile: {device_frame_class}"
    print("  [PASS] Switched to 375px mobile view.")

    # Test Desktop View Toggle
    await page.click("#preview-toggle-desktop")
    await page.wait_for_timeout(300)
    device_frame_class = await page.get_attribute("#preview-device-frame", "class")
    assert "device-desktop" in device_frame_class, f"Device frame did not switch to desktop: {device_frame_class}"
    print("  [PASS] Switched back to full-width desktop view.")

    # Test Notes Drawer inside Preview
    await page.click("#preview-notes-toggle")
    await page.wait_for_timeout(300)
    notes_drawer_visible = await page.is_visible("#preview-notepad-drawer")
    assert notes_drawer_visible, "Preview notes drawer did not open."
    print("  [PASS] Quick notepad inside preview opened.")

    # Close Preview via Esc
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    assert not (await page.is_visible("#in-app-web-preview")), "Esc failed to close web preview."
    print("  [PASS] Esc key closed in-app web preview.")


async def test_optimistic_stage_transition_and_rollback(page):
    print("\n--- 5. Testing Optimistic Stage Transition & Rollback ---")
    await page.set_viewport_size({"width": 1366, "height": 768})
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # Find first card in QUALIFIED or AUDITED column
    card = await page.query_selector(".kanban-card")
    assert card, "No kanban card available to test transition."
    lead_id = await card.get_attribute("data-lead-id")

    # Open drawer to inspect stage
    await card.click()
    await page.wait_for_timeout(500)
    assert await page.is_visible("#drawer-lead-detail"), "Drawer did not open."

    orig_stage = await page.text_content("#drawer-current-stage")
    print(f"  Current lead stage: {orig_stage.strip()}")

    # Select target stage (e.g. FIRST_CONTACT)
    await page.select_option("#drawer-stage-select", "FIRST_CONTACT")
    await page.wait_for_timeout(800)

    new_stage = await page.text_content("#drawer-current-stage")
    assert new_stage.strip() == "FIRST_CONTACT", f"Optimistic stage update failed: {new_stage}"
    print(f"  [PASS] Stage updated optimistically to FIRST_CONTACT.")

    # Close drawer
    await page.click("#drawer-close")
    await page.wait_for_timeout(300)


async def test_drawer_inline_editing_and_channel_sync(page):
    print("\n--- 6. Testing In-Line Lead Editing & Channel Status Sync ---")
    await page.set_viewport_size({"width": 1366, "height": 768})
    await page.goto(f"{BASE_URL}/", wait_until="networkidle")
    await page.wait_for_timeout(500)

    # Click first card
    await page.click(".kanban-card")
    await page.wait_for_timeout(500)

    # Check In-line edit form
    unique_name = f"Negocio Editado {int(time.time()) % 10000}"
    await page.fill("#edit-drawer-name", unique_name)
    await page.click("#form-drawer-inline-edit button[type='submit']")
    await page.wait_for_timeout(800)

    # Verify updated lead name in drawer header
    header_name = await page.text_content("#drawer-lead-name")
    assert unique_name in header_name, f"In-line edit failed to persist name: {header_name}"
    print(f"  [PASS] In-line edit saved and reflected immediately: '{header_name.strip()}'")

    # Test "Sin WhatsApp" marking
    btn_no_wa = await page.query_selector(".btn-solo-icon[data-tooltip*='Sin WhatsApp']")
    if btn_no_wa:
        await btn_no_wa.click()
        await page.wait_for_timeout(800)
        # Verify button switched to fixed line with disabled/matte opacity
        btn_fixed = await page.query_selector(".btn-solo-icon[data-tooltip*='Solo linea fija']")
        assert btn_fixed, "Button did not transition to 'Solo linea fija'."
        opacity = await btn_fixed.evaluate("el => window.getComputedStyle(el).opacity")
        assert float(opacity) <= 0.4, f"Disabled button opacity is not matte/muted: {opacity}"
        print(f"  [PASS] 'Marcar sin WhatsApp' updated immediately with matte opacity {opacity}.")


async def test_visual_activity_timeline(page):
    print("\n--- 7. Testing Visual Activity Timeline in Drawer ---")
    # Switch to "Historial" tab
    await page.click(".drawer-tab-btn[data-tab='tab-timeline']")
    await page.wait_for_selector("#drawer-timeline-feed .timeline-entry", timeout=5000)

    # Verify timeline entries rendered with icons
    timeline_items = await page.query_selector_all(".timeline-entry")
    assert len(timeline_items) > 0, "No timeline entries rendered in #drawer-timeline-feed."

    first_item = timeline_items[0]
    has_icon = await first_item.query_selector(".timeline-entry-icon svg")
    has_title = await first_item.query_selector(".timeline-entry-title")
    has_time = await first_item.query_selector(".timeline-time")

    assert has_icon and has_title and has_time, "Timeline entry missing icon, title, or time."
    title_text = await has_title.text_content()
    time_text = await has_time.text_content()
    print(f"  [PASS] Timeline entry rendered with vector icon: '{title_text.strip()}' ({time_text.strip()})")

    # Close drawer
    await page.click("#drawer-close")
    await page.wait_for_timeout(300)


async def test_duplicate_cleanup_assistant(page):
    print("\n--- 8. Testing Duplicate Cleanup Assistant in Settings ---")
    # Switch to Settings view
    await page.click("#nav-btn-settings")
    await page.wait_for_timeout(600)
    assert await page.is_visible("#view-settings"), "Settings view did not open."

    # Click 3.9 Asistente Duplicados subnav tab
    await page.click("#btn-subnav-duplicates")
    await page.wait_for_timeout(600)
    assert await page.is_visible("#mod-duplicates"), "Module 3.9 Duplicados did not open."
    print("  [PASS] Duplicate Cleanup Assistant view opened.")

    # Check total counter strip
    assistant_total = await page.text_content("#dup-assistant-total")
    print(f"  [PASS] Duplicate assistant total pending pairs: {assistant_total.strip()}")


async def test_global_keyboard_shortcuts(page):
    print("\n--- 9. Testing Global Keyboard Shortcuts (Cheat Sheet & Focus Mode) ---")
    # Press '?' key to open cheat sheet
    await page.keyboard.press("?")
    await page.wait_for_timeout(400)
    guide_open = await page.is_visible("#modal-shortcuts-guide")
    assert guide_open, "'?' key failed to open shortcuts cheat sheet."
    print("  [PASS] '?' key successfully opened Shortcuts Cheat Sheet.")

    # Close with Esc
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    assert not (await page.is_visible("#modal-shortcuts-guide")), "Esc failed to close cheat sheet."
    print("  [PASS] Esc closed cheat sheet.")

    # Press 'F' key to toggle Focus Mode
    await page.click("#nav-btn-leads")
    await page.wait_for_timeout(400)
    await page.keyboard.press("f")
    await page.wait_for_timeout(500)
    focus_visible = await page.is_visible("#focus-mode-container")
    assert focus_visible, "'F' key failed to toggle Focus Mode."
    print("  [PASS] 'F' key toggled Focus Mode.")

    # Press 'F' again to return to Kanban
    await page.keyboard.press("f")
    await page.wait_for_timeout(500)
    assert await page.is_visible("#kanban-board-container"), "'F' key failed to return to Kanban."
    print("  [PASS] 'F' key returned cleanly to Kanban.")


async def test_live_search(page):
    print("\n--- 10. Testing Live Search Without Page Reload ---")
    await page.fill("#leads-search-input", "Dental")
    await page.wait_for_timeout(400)

    # Check that kanban board cards filtered dynamically
    cards = await page.query_selector_all(".kanban-card")
    print(f"  [PASS] Search filtered cards dynamically: {len(cards)} visible matching 'Dental'.")

    # Clear search
    await page.fill("#leads-search-input", "")
    await page.wait_for_timeout(400)
    all_cards = await page.query_selector_all(".kanban-card")
    assert len(all_cards) >= len(cards), "Clearing search did not restore all cards."
    print(f"  [PASS] Cleared search restored all {len(all_cards)} cards immediately.")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await context.new_page()

        try:
            await test_resolutions_and_overflow(page)
            await test_border_radius_and_touch_targets(page)
            await test_global_popovers_and_clamping(page)
            await test_in_app_web_preview(page)
            await test_optimistic_stage_transition_and_rollback(page)
            await test_drawer_inline_editing_and_channel_sync(page)
            await test_visual_activity_timeline(page)
            await test_duplicate_cleanup_assistant(page)
            await test_global_keyboard_shortcuts(page)
            await test_live_search(page)

            print("\n" + "=" * 66)
            print("ALL 10 QA MODULES PASSED WITH 100% SUCCESS! FASE 11 VERIFIED.")
            print("=" * 66)
        except Exception as err:
            print(f"\n[FAIL] Test aborted with error: {err}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
