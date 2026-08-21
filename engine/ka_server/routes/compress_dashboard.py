"""
routes/compress_dashboard.py — Dashboard de la compression HCV.

Endpoints
---------
GET  /api/compress/dashboard/stats    → statistiques agrégées
GET  /api/compress/dashboard/history  → historique des compressions (?limit=N)
POST /api/compress/dashboard/reset    → vide l'historique (dev/demo)

# GhostCompressor (KA Storage Saver)
GET  /api/compress/storage/scan       → analyse le téléphone (nb fichiers, taille, projection)
POST /api/compress/storage/activate   → lance GhostCompressor en arrière-plan
POST /api/compress/storage/deactivate → arrête GhostCompressor
GET  /api/compress/storage/status     → stats temps réel du GhostCompressor
POST /api/compress/storage/restore    → restaure un fichier depuis la corbeille {filename}
POST /api/compress/storage/restore-all → restaure tous les originaux de la corbeille
"""

import traceback
from flask import request, jsonify

from ka_server.services.compress_store import get_stats, get_history, reset_history


def register_compress_dashboard_routes(app, services):
    """Enregistre les routes du dashboard de compression."""

    @app.route('/api/compress/dashboard/stats', methods=['GET'])
    def api_compress_dashboard_stats():
        """Statistiques agrégées de toutes les compressions."""
        return jsonify(get_stats())

    @app.route('/api/compress/dashboard/history', methods=['GET'])
    def api_compress_dashboard_history():
        """Historique des compressions (plus récentes d'abord)."""
        try:
            limit = min(int(request.args.get('limit', 100)), 500)
        except (TypeError, ValueError):
            limit = 100
        return jsonify({
            'history': get_history(limit=limit),
            'count': len(get_history(limit=limit)),
        })

    @app.route('/api/compress/dashboard/reset', methods=['POST', 'OPTIONS'])
    def api_compress_dashboard_reset():
        """Vide l'historique (utile en démo)."""
        if request.method == 'OPTIONS':
            return '', 200
        removed = reset_history()
        return jsonify({'success': True, 'removed': removed})

    # ═══════════════════════════════════════════════════════════════════════
    # STORAGE SAVER — GhostCompressor
    # ═══════════════════════════════════════════════════════════════════════

    _ghost_ref = {'instance': None}

    def _get_ghost():
        """Import et retourne le singleton GhostCompressor."""
        if _ghost_ref['instance'] is None:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from ka_background_compress import get_ghost
                _ghost_ref['instance'] = get_ghost()
            except Exception as e:
                raise RuntimeError(f"Impossible de charger GhostCompressor : {e}")
        return _ghost_ref['instance']

    @app.route('/api/compress/storage/scan', methods=['GET'])
    def api_storage_scan():
        """Analyse le téléphone : fichiers trouvés, taille totale, projection."""
        try:
            g = _get_ghost()
            import os, fnmatch
            from pathlib import Path

            watch = g.watch_dir
            image_exts = ('*.jpg', '*.jpeg', '*.png', '*.heic', '*.webp')
            video_exts = ('*.mp4', '*.avi', '*.mov', '*.mkv', '*.m4v')
            all_exts = image_exts + video_exts

            files = []
            total_size = 0
            for pattern in all_exts:
                for fp in Path(watch).rglob(pattern):
                    if fp.is_file():
                        sz = fp.stat().st_size
                        rel = str(fp.relative_to(watch))
                        total_size += sz
                        files.append({
                            'name': rel,
                            'size': sz,
                            'ext': fp.suffix.lower(),
                        })

            # Stats du ghost déjà en cours
            ghost_stats = g.stats()
            projection = ghost_stats.get('projection', {})

            # Combien d'espace pourrait être économisé (estimation ratio ×8)
            estimated_ratio = projection.get('avg_ratio', 8) if projection.get('avg_ratio') != '—' else 8
            saved_estimate = round(total_size * (1 - 1 / max(estimated_ratio, 2)), 2)

            return jsonify({
                'success': True,
                'total_files': len(files),
                'total_size': total_size,
                'total_size_fmt': _fmt_bytes(total_size),
                'saved_estimate': saved_estimate,
                'saved_estimate_fmt': _fmt_bytes(saved_estimate),
                'estimated_ratio': estimated_ratio,
                'files': files[:50],  # limite à 50 fichiers pour la réponse
                'files_truncated': len(files) > 50,
                'already_compressed': ghost_stats['files_count'],
                'watch_dir': watch,
            })
        except Exception as e:
            return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

    @app.route('/api/compress/storage/activate', methods=['POST', 'OPTIONS'])
    def api_storage_activate():
        """Lance GhostCompressor en arrière-plan."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            g = _get_ghost()
            g.start()
            return jsonify({'success': True, 'status': 'active', 'watch_dir': g.watch_dir})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/compress/storage/deactivate', methods=['POST', 'OPTIONS'])
    def api_storage_deactivate():
        """Arrête GhostCompressor."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            g = _get_ghost()
            g.stop()
            return jsonify({'success': True, 'status': 'stopped'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/compress/storage/status', methods=['GET'])
    def api_storage_status():
        """Statistiques en temps réel du GhostCompressor."""
        try:
            g = _get_ghost()
            s = g.stats()
            return jsonify({
                'success': True,
                'active': g._running if hasattr(g, '_running') else False,
                'files_count': s['files_count'],
                'total_original_bytes': s['total_original_bytes'],
                'total_compressed_bytes': s['total_compressed_bytes'],
                'total_saved_bytes': s['total_original_bytes'] - s['total_compressed_bytes'],
                'total_original_fmt': _fmt_bytes(s['total_original_bytes']),
                'total_compressed_fmt': _fmt_bytes(s['total_compressed_bytes']),
                'total_saved_fmt': _fmt_bytes(s['total_original_bytes'] - s['total_compressed_bytes']),
                'free_space_gb': s.get('free_space_gb', 0),
                'projection': s.get('projection', {}),
                'compressed': dict(list(s.get('compressed', {}).items())[:20]),
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/compress/storage/restore', methods=['POST', 'OPTIONS'])
    def api_storage_restore():
        """Restaure un fichier depuis la corbeille."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            body = request.get_json(silent=True)
            if not body or 'filename' not in body:
                return jsonify({'error': "JSON avec 'filename' requis"}), 400
            g = _get_ghost()
            ok = g.restore_file(body['filename'])
            return jsonify({'success': ok, 'filename': body['filename']})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/compress/storage/restore-all', methods=['POST', 'OPTIONS'])
    def api_storage_restore_all():
        """Restaure tous les originaux de la corbeille."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            g = _get_ghost()
            import os
            trash = g.trash_dir
            restored = []
            for root, _, files in os.walk(trash):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.isfile(fp):
                        # Reconstruire le chemin relatif depuis trash_dir
                        rel = os.path.relpath(fp, trash)
                        if g.restore_file(rel):
                            restored.append(rel)
            return jsonify({'success': True, 'restored_count': len(restored), 'files': restored[:30]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/compress/storage/clean-trash', methods=['POST', 'OPTIONS'])
    def api_storage_clean_trash():
        """Supprime les fichiers en corbeille de plus de 7 jours."""
        if request.method == 'OPTIONS':
            return '', 200
        try:
            g = _get_ghost()
            g.clean_trash()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} o"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} Ko"
    if n < 1024 ** 3:
        return f"{n / 1024 ** 2:.1f} Mo"
    return f"{n / 1024 ** 3:.2f} Go"
