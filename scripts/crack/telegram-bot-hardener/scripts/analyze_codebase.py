#!/usr/bin/env python3
"""
analyze_codebase.py — Analiza un bot de Telegram (aiogram 3) en busca de patrones frágiles.

Uso:
    python analyze_codebase.py <ruta_del_proyecto>
    python analyze_codebase.py .
"""

import ast
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Issue:
    severity: str  # "CRITICAL", "WARNING", "INFO"
    file: str
    line: Optional[int]
    message: str
    suggestion: str


@dataclass
class AnalysisReport:
    issues: list[Issue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def add(self, severity, file, line, message, suggestion):
        self.issues.append(Issue(severity, file, line, message, suggestion))

    def critical(self):
        return [i for i in self.issues if i.severity == "CRITICAL"]

    def warnings(self):
        return [i for i in self.issues if i.severity == "WARNING"]

    def info(self):
        return [i for i in self.issues if i.severity == "INFO"]


def find_python_files(root: Path) -> list[Path]:
    return [
        p for p in root.rglob("*.py")
        if not any(part in p.parts for part in ["__pycache__", ".venv", "venv", "node_modules"])
    ]


def analyze_file(filepath: Path, report: AnalysisReport):
    rel_path = str(filepath)
    
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        report.add("WARNING", rel_path, None, f"No se pudo parsear: {e}", "Revisar manualmente")
        return

    lines = source.splitlines()

    # ── 1. Funciones muy largas ──────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_lines = (node.end_lineno or node.lineno) - node.lineno
            if func_lines > 60:
                report.add(
                    "WARNING", rel_path, node.lineno,
                    f"Función '{node.name}' tiene {func_lines} líneas (>60)",
                    "Extraer en sub-funciones o mover lógica a un Service"
                )
            elif func_lines > 40:
                report.add(
                    "INFO", rel_path, node.lineno,
                    f"Función '{node.name}' tiene {func_lines} líneas (>40)",
                    "Considerar dividir si la función hace más de una cosa"
                )

    # ── 2. Except genérico (captura silenciosa) ──────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                report.add(
                    "CRITICAL", rel_path, node.lineno,
                    "except: sin tipo captura todo silenciosamente",
                    "Usar 'except Exception as e: logger.error(e)' con tipo específico"
                )
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                # Verificar si el cuerpo solo tiene 'pass' o similar
                body_stmts = node.body
                if len(body_stmts) == 1 and isinstance(body_stmts[0], ast.Pass):
                    report.add(
                        "CRITICAL", rel_path, node.lineno,
                        "except Exception: pass — error silenciado completamente",
                        "Al menos loggear: logger.error('Error en X', exc_info=True)"
                    )

    # ── 3. Variables globales mutables ───────────────────────────
    # Construir mapa de padres una sola vez para este archivo
    parent_map: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[id(child)] = parent

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            value = node.value
            if isinstance(value, (ast.Dict, ast.List, ast.Set)):
                name = node.targets[0].id
                if not name.startswith("_") and not name.isupper():
                    # Verificar si está dentro de una función usando el mapa de padres
                    parent = parent_map.get(id(node))
                    inside_function = False
                    while parent is not None:
                        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            inside_function = True
                            break
                        parent = parent_map.get(id(parent))
                    if not inside_function:
                        report.add(
                            "WARNING", rel_path, node.lineno,
                            f"Variable global mutable '{name}' (dict/list/set al nivel de módulo)",
                            "Encapsular en clase o pasar como dependencia para evitar estado compartido"
                        )

    # ── 4. Lógica de negocio en handlers aiogram ─────────────────
    aiogram_handler_decorators = {"message_handler", "callback_query_handler", "router"}
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Buscar funciones con parámetros típicos de handlers (message, callback, call)
            param_names = [arg.arg for arg in node.args.args]
            is_handler = any(p in ("message", "callback", "call", "query", "event") for p in param_names)
            
            if is_handler:
                func_lines = (node.end_lineno or node.lineno) - node.lineno
                if func_lines > 20:
                    report.add(
                        "WARNING", rel_path, node.lineno,
                        f"Handler '{node.name}' ({func_lines} líneas) contiene probablemente lógica de negocio",
                        "Mover la lógica a un Service; el handler debe tener <15 líneas"
                    )

    # ── 5. Imports entre módulos del mismo sistema (acoplamiento) ─
    known_modules = ["gamification", "narrative", "channel_admin", "minigame"]
    imports_found = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = ", ".join(alias.name for alias in node.names)
            
            for mod in known_modules:
                if mod in module and mod not in rel_path:
                    imports_found.append((node.lineno, module))

    if len(imports_found) > 2:
        for lineno, module in imports_found:
            report.add(
                "WARNING", rel_path, lineno,
                f"Import cruzado de '{module}' desde módulo diferente",
                "Usar Event Bus o inyección de dependencias en vez de imports directos"
            )

    # ── 6. Ausencia de type hints (solo si --type-hints) ────────
    if report.stats.get("check_type_hints"):
        fns_no_hints = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                no_return = node.returns is None
                no_args = [a.arg for a in node.args.args if a.annotation is None and a.arg != "self"]
                if no_return or no_args:
                    fns_no_hints.append(node.name)
        if fns_no_hints:
            sample = ", ".join(fns_no_hints[:5]) + ("..." if len(fns_no_hints) > 5 else "")
            report.add(
                "INFO", rel_path, None,
                f"{len(fns_no_hints)} funciones sin type hints ({sample})",
                "Agregar type hints mejora la detectabilidad de bugs"
            )

    # ── 7. Detección de TODOs y FIXMEs ───────────────────────────
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            upper = stripped.upper()
            if "TODO" in upper or "FIXME" in upper or "HACK" in upper:
                report.add(
                    "INFO", rel_path, i,
                    f"Deuda técnica marcada: {stripped[:80]}",
                    "Revisar y crear ticket o issue para no perder track"
                )


def detect_circular_imports(files: list[Path], root: Path) -> list[tuple]:
    """Detecta posibles imports circulares entre módulos."""
    import_graph: dict[str, set[str]] = {}
    
    for filepath in files:
        rel = str(filepath.relative_to(root)).replace("/", ".").replace(".py", "")
        import_graph[rel] = set()
        
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # Normalizar a path relativo si es posible
                    mod = node.module
                    import_graph[rel].add(mod)
        except Exception:
            pass
    
    # Detección simple de ciclos directos A → B → A
    cycles = []
    for mod_a, deps_a in import_graph.items():
        for mod_b in deps_a:
            if mod_b in import_graph and mod_a in import_graph.get(mod_b, set()):
                pair = tuple(sorted([mod_a, mod_b]))
                if pair not in cycles:
                    cycles.append(pair)
    
    return cycles


def print_report(report: AnalysisReport, root: Path):
    print("\n" + "="*70)
    print("  REPORTE DE ANÁLISIS — Telegram Bot Hardener")
    print("="*70)

    criticals = report.critical()
    warnings  = report.warnings()
    infos     = report.info()

    print(f"\n📊 Archivos analizados: {report.stats.get('files', 0)}")
    print(f"   🔴 Críticos:  {len(criticals)}")
    print(f"   🟡 Warnings:  {len(warnings)}")
    print(f"   🔵 Info:      {len(infos)}")

    if criticals:
        print("\n" + "─"*70)
        print("🔴 CRÍTICOS — Resolver antes de cualquier cambio")
        print("─"*70)
        for issue in criticals:
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"\n  [{loc}]")
            print(f"  Problema:   {issue.message}")
            print(f"  Solución:   {issue.suggestion}")

    if warnings:
        print("\n" + "─"*70)
        print("🟡 WARNINGS — Fragilidad potencial")
        print("─"*70)
        for issue in warnings:
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"\n  [{loc}]")
            print(f"  Problema:   {issue.message}")
            print(f"  Solución:   {issue.suggestion}")

    if infos:
        print("\n" + "─"*70)
        print("🔵 INFO — Deuda técnica y mejoras")
        print("─"*70)
        for issue in infos:
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"  [{loc}] {issue.message}")

    # ── Próximos pasos dinámicos basados en hallazgos reales ─────
    print("\n" + "="*70)
    print("  PRÓXIMOS PASOS RECOMENDADOS")
    print("="*70)

    steps: list[tuple[str, list[str]]] = []

    # Paso 1: críticos reales encontrados
    critical_actions = []
    msgs = [i.message for i in criticals]
    if any("except" in m for m in msgs):
        critical_actions.append("Eliminar todos los 'except: pass/Exception' — cada uno es un bug silenciado")
    if any("circular" in m.lower() for m in msgs):
        critical_actions.append("Romper imports circulares detectados usando Event Bus o inyección de dependencias")
    if critical_actions:
        critical_actions.insert(0, "Agregar ErrorHandlerMiddleware global (references/architecture-patterns.md §3)")
        steps.append(("🔴 Prioridad 1 — Críticos", critical_actions))

    # Paso 2: estructura — basado en warnings reales
    structure_actions = []
    warn_msgs = [i.message for i in warnings]
    if any("Handler" in m and "líneas" in m for m in warn_msgs):
        handlers_affected = [i.file.split("/")[-1] for i in warnings if "Handler" in i.message]
        unique_files = list(dict.fromkeys(handlers_affected))[:4]
        structure_actions.append(
            f"Extraer lógica de negocio de handlers a Services en: {', '.join(unique_files)}"
        )
    if any("Import cruzado" in m for m in warn_msgs):
        crossed = list({i.file.split("/")[-1] for i in warnings if "Import cruzado" in i.message})
        structure_actions.append(f"Desacoplar imports cruzados en: {', '.join(crossed[:3])}")
    if any("global mutable" in m for m in warn_msgs):
        structure_actions.append("Encapsular variables globales mutables en clases o inyectarlas como dependencias")
    if structure_actions:
        steps.append(("🟡 Prioridad 2 — Estructura", structure_actions))

    # Paso 3: tests — siempre recomendado, con contexto de lo encontrado
    test_actions = [
        "Instalar: pip install pytest pytest-asyncio pytest-mock",
        "Crear tests/conftest.py con fixtures de bot, mensaje y callback mockeados",
    ]
    service_files = [i.file.split("/")[-1] for i in warnings if "Handler" in i.message]
    unique_services = list(dict.fromkeys(service_files))[:3]
    if unique_services:
        test_actions.append(f"Escribir tests unitarios para los Services extraídos de: {', '.join(unique_services)}")
    else:
        test_actions.append("Escribir tests unitarios para gamification_service, narrative_service, channel_admin_service")
    steps.append(("🔵 Prioridad 3 — Tests", test_actions))

    if not steps:
        print("\n  ✅ No se encontraron problemas críticos ni estructurales. Pasar directo a tests.")
    else:
        for title, actions in steps:
            print(f"\n  {title}:")
            for a in actions:
                print(f"  - {a}")

    print()


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-") and len(args) == 1:
        print("Uso: python analyze_codebase.py <ruta_del_proyecto> [--type-hints]")
        sys.exit(1)

    check_type_hints = "--type-hints" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print("Error: especifica la ruta del proyecto.")
        sys.exit(1)

    root = Path(paths[0]).resolve()
    if not root.exists():
        print(f"Error: La ruta '{root}' no existe.")
        sys.exit(1)

    print(f"\n🔍 Analizando: {root}")
    if check_type_hints:
        print("   (mode: incluir análisis de type hints)")

    files = find_python_files(root)
    report = AnalysisReport()
    report.stats["files"] = len(files)
    report.stats["check_type_hints"] = check_type_hints

    for filepath in files:
        analyze_file(filepath, report)

    # Detección de imports circulares
    cycles = detect_circular_imports(files, root)
    if cycles:
        for cycle in cycles:
            report.add(
                "CRITICAL", f"{cycle[0]} ↔ {cycle[1]}", None,
                f"Posible import circular entre módulos: {cycle[0]} y {cycle[1]}",
                "Usar Event Bus o inyección de dependencias para romper el ciclo"
            )

    print_report(report, root)


if __name__ == "__main__":
    main()
