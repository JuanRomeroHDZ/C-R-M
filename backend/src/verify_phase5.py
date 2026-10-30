import sys
from datetime import datetime, timezone, timedelta
from uuid import UUID
from src.db.connection import execute_query
from src.pipeline.state_machine import (
    STAGES,
    VALID_STAGES,
    REGRET_REASONS,
    LOSS_REASONS,
    transition_stage,
    check_duplicate,
    soft_delete_lead,
    restore_lead,
    reset_lead_history,
)


def run_phase5_verification():
    print("====================================================================")
    print("VERIFICACION INTEGRAL DE LA FASE 5: PIPELINE COMERCIAL Y MÁQUINA DE ESTADOS")
    print("====================================================================")

    # 1. Verify 12 stages definition
    print(f"[TEST 1] Verificando definicion exacta de las 12 fases...")
    assert len(STAGES) == 12, f"Se esperaban 12 fases, encontradas {len(STAGES)}"
    expected_stages = [
        "EXTRACTED", "AUDITED", "QUALIFIED", "FIRST_CONTACT", "REPLY_RECEIVED",
        "IN_CONVERSATION", "PROPOSAL_PRESENTED", "IN_NEGOTIATION", "POSTPONED",
        "REGRETTED", "CLOSED_WON", "CLOSED_LOST"
    ]
    for idx, expected in enumerate(expected_stages):
        assert STAGES[idx]["slug"] == expected, f"Fase en posicion {idx} deberia ser {expected}"
    print("  OK: 12 fases validadas en orden estricto.")

    # 2. Select a real lead from Tijuana
    rows = execute_query("SELECT id, name, lifecycle_stage, phone_e164 FROM leads WHERE is_deleted = FALSE LIMIT 1;")
    assert len(rows) > 0, "No se encontraron prospectos en la base de datos."
    lead = rows[0]
    lead_id = lead["id"]
    print(f"[TEST 2] Prospecto real seleccionado para pruebas: {lead['name']} ({lead_id})")

    # 3. Transition to POSTPONED without date -> must fail
    print("[TEST 3] Validando regla obligatoria en fase POSTPONED (requiere fecha y nota)...")
    try:
        transition_stage(lead_id, "POSTPONED")
        print("  FALLA: Debio fallar sin fecha de reactivacion")
        sys.exit(1)
    except Exception as e:
        print(f"  OK: Rechazo esperado sin fecha -> {getattr(e, 'detail', str(e))}")

    # 4. Valid transition to POSTPONED -> creates calendar event
    reactivation_target = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    res_postponed = transition_stage(
        lead_id,
        "POSTPONED",
        notes="Seguimiento pospuesto tras primera llamada",
        reactivation_date=reactivation_target
    )
    assert res_postponed["to_stage"] == "POSTPONED"
    print(f"  OK: Transicion a POSTPONED exitosa. Duracion calculada: {res_postponed['duration_seconds']}s")

    # Check calendar event was created
    evts = execute_query(
        "SELECT id, title, event_type, start_time FROM calendar_events WHERE lead_id = %s ORDER BY created_at DESC LIMIT 1;",
        (str(lead_id),)
    )
    assert len(evts) > 0, "No se genero el evento automatico en el calendario."
    print(f"  OK: Evento de calendario autogenerado -> {evts[0]['title']}")

    # 5. Transition to REGRETTED without reason -> must fail
    print("[TEST 5] Validando regla obligatoria en fase REGRETTED (requiere motivo)...")
    try:
        transition_stage(lead_id, "REGRETTED")
        print("  FALLA: Debio fallar sin motivo de arrepentimiento")
        sys.exit(1)
    except Exception as e:
        print(f"  OK: Rechazo esperado sin motivo -> {getattr(e, 'detail', str(e))}")

    # 6. Valid transition to REGRETTED
    res_regret = transition_stage(
        lead_id,
        "REGRETTED",
        regret_reason="Presupuesto insuficiente",
        regret_amount=18000.0,
        regret_service="Desarrollo Web y SEO Local",
        notes="Cliente pausado por reestructuracion presupuestaria"
    )
    assert res_regret["to_stage"] == "REGRETTED"
    print("  OK: Transicion a REGRETTED exitosa con motivo registrado.")

    # 7. Transition to CLOSED_LOST without reason -> must fail
    print("[TEST 7] Validando regla obligatoria en fase CLOSED_LOST (requiere motivo)...")
    try:
        transition_stage(lead_id, "CLOSED_LOST")
        print("  FALLA: Debio fallar sin motivo de descarte")
        sys.exit(1)
    except Exception as e:
        print(f"  OK: Rechazo esperado sin motivo -> {getattr(e, 'detail', str(e))}")

    # 8. Valid transition to CLOSED_LOST
    res_lost = transition_stage(
        lead_id,
        "CLOSED_LOST",
        loss_reason="No le interesa",
        notes="Prefiere continuar sin presencia digital"
    )
    assert res_lost["to_stage"] == "CLOSED_LOST"
    print("  OK: Transicion a CLOSED_LOST exitosa con motivo registrado.")

    # 9. Verify history duration tracking
    hist = execute_query(
        "SELECT from_stage, to_stage, duration_seconds, notes FROM lead_stage_history WHERE lead_id = %s ORDER BY created_at DESC;",
        (str(lead_id),)
    )
    assert len(hist) >= 3, "El historial de transiciones no registro todos los movimientos."
    print(f"  OK: {len(hist)} transiciones trazadas con duracion en segundos.")

    # 10. Test Duplicate Prevention in real-time
    print("[TEST 10] Validando motor de prevencion absoluta de duplicados...")
    dup_res = check_duplicate(phone_e164=lead.get("phone_e164"))
    if lead.get("phone_e164"):
        assert dup_res and dup_res["is_duplicate"], "No detecto colision de telefono existente."
        print(f"  OK: Colision detectada en {dup_res['conflict_field']} con id {dup_res['existing_lead']['id']}")
    else:
        dup_name = check_duplicate(name=lead["name"])
        assert dup_name and dup_name["is_duplicate"], "No detecto colision de nombre existente."
        print(f"  OK: Colision detectada en nombre con id {dup_name['existing_lead']['id']}")

    # 11. Test Soft Delete & Blacklist Immunity
    print("[TEST 11] Validando borrado logico (Soft Delete) y blindaje en lista negra...")
    del_res = soft_delete_lead(lead_id, reason="Prueba de auditoria tecnica Fase 5")
    assert del_res["status"] == "DELETED"

    # Verify lead is marked deleted
    chk = execute_query("SELECT is_deleted, deleted_at, deleted_reason FROM leads WHERE id = %s;", (str(lead_id),))[0]
    assert chk["is_deleted"] is True
    print("  OK: Prospecto marcado como is_deleted = TRUE con fecha de borrado.")

    # Verify duplicate check detects lead even when deleted
    dup_trash = check_duplicate(name=lead["name"])
    assert dup_trash and dup_trash["is_duplicate"] and dup_trash["existing_lead"]["is_deleted"] is True
    print("  OK: Detector de duplicados reconoce que el contacto existe en papelera.")

    # 12. Test Restore
    print("[TEST 12] Validando restauracion desde papelera...")
    rest_res = restore_lead(lead_id)
    assert rest_res["status"] == "RESTORED"
    chk_restored = execute_query("SELECT is_deleted FROM leads WHERE id = %s;", (str(lead_id),))[0]
    assert chk_restored["is_deleted"] is False
    print("  OK: Prospecto restaurado correctamente al pipeline activo.")

    # 13. Test Reset History
    print("[TEST 13] Validando reinicio de historial y actividad...")
    reset_res = reset_lead_history(lead_id)
    assert reset_res["status"] == "RESET"
    chk_reset = execute_query("SELECT lifecycle_stage FROM leads WHERE id = %s;", (str(lead_id),))[0]
    assert chk_reset["lifecycle_stage"] == "QUALIFIED"
    hist_after = execute_query("SELECT count(*) as count FROM lead_stage_history WHERE lead_id = %s;", (str(lead_id),))[0]
    assert hist_after["count"] == 0
    print("  OK: Historial reiniciado a 0 y fase restablecida a QUALIFIED.")

    print("====================================================================")
    print("TODAS LAS 13 PRUEBAS DE LA FASE 5 PASARON EXITOSAMENTE.")
    print("====================================================================")


if __name__ == "__main__":
    run_phase5_verification()
