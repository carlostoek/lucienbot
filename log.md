2026-04-07T04:44:46.736506399Z [info] 2026-04-07 04:44:46,459 - apscheduler.executors.default - INFO - Job "Approve pending join requests (trigger: interval[0:00:30], next run at: 2026-04-07 04:45:16 UTC)" executed successfully
2026-04-07T04:44:47.073589784Z [info] 2026-04-07 04:44:47,068 - services.besito_service - INFO - Acreditados 2 besitos a usuario 779876234 - reaction
2026-04-07T04:44:47.073595793Z [info] 2026-04-07 04:44:47,069 - services.broadcast_service - INFO - Reacción registrada: user=779876234, broadcast=6, besitos=2
2026-04-07T04:44:47.116269784Z [info] 2026-04-07 04:44:47,095 - services.mission_service - INFO - Mision completada: user=779876234, mission=3
2026-04-07T04:44:47.128903150Z [info] 2026-04-07 04:44:47,122 - services.besito_service - INFO - Acreditados 5 besitos a usuario 779876234 - mission
2026-04-07T04:44:47.140000546Z [info] 2026-04-07 04:44:47,136 - services.mission_service - INFO - Recompensa entregada: user=779876234, reward=2
2026-04-07T04:44:47.225108143Z [info] 2026-04-07 04:44:47,220 - services.mission_service - INFO - Mision completada: user=779876234, mission=6
2026-04-07T04:44:47.731652250Z [info] 2026-04-07 04:44:47,256 - aiogram.event - INFO - Update id=277619263 is handled. Duration 522 ms by bot id=7360762013
2026-04-07T04:44:48.039746462Z [info] 2026-04-07 04:44:48,036 - services.package_service - INFO - Paquete 12 entregado a usuario 779876234
2026-04-07T04:44:48.039753118Z [info] 2026-04-07 04:44:48,036 - services.mission_service - INFO - Recompensa entregada: user=779876234, reward=7
2026-04-07T04:44:48.044645992Z [info] 2026-04-07 04:44:48,040 - services.broadcast_service - INFO - Misiones completadas por reacción: user=779876234, count=2
2026-04-07T04:44:48.895061325Z [info] 2026-04-07 04:44:48,883 - aiogram.event - INFO - Update id=277619265 is not handled. Duration 21 ms by bot id=7360762013
2026-04-07T04:44:48.895072187Z [info] 2026-04-07 04:44:48,884 - aiogram.event - ERROR - Cause exception while process update id=277619265 by bot id=7360762013
2026-04-07T04:44:48.895078702Z [info] TypeError: can't subtract offset-naive and offset-aware datetimes
2026-04-07T04:44:48.895088087Z [info] Traceback (most recent call last):
2026-04-07T04:44:48.895095067Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/dispatcher.py", line 320, in _process_update
2026-04-07T04:44:48.895101703Z [info]     response = await self.feed_update(bot, update, **kwargs)
2026-04-07T04:44:48.895109458Z [info]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.895116498Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/dispatcher.py", line 164, in feed_update
2026-04-07T04:44:48.895122678Z [info]     response = await self.update.wrap_outer_middleware(
2026-04-07T04:44:48.895128662Z [info]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.895134003Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/middlewares/error.py", line 27, in __call__
2026-04-07T04:44:48.895140071Z [info]     return await handler(event, data)
2026-04-07T04:44:48.895146709Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.895152716Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/middlewares/user_context.py", line 58, in __call__
2026-04-07T04:44:48.895158787Z [info]     return await handler(event, data)
2026-04-07T04:44:48.895165308Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.895171260Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/fsm/middleware.py", line 43, in __call__
2026-04-07T04:44:48.895177597Z [info]     return await handler(event, data)
2026-04-07T04:44:48.922095234Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.922100019Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/event/telegram.py", line 126, in trigger
2026-04-07T04:44:48.922104562Z [info]     return await wrapped_inner(event, kwargs)
2026-04-07T04:44:48.922109468Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/dispatcher.py", line 283, in _listen_update
2026-04-07T04:44:48.922110560Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.922116121Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/event/handler.py", line 71, in call
2026-04-07T04:44:48.922122700Z [info]     return await self.propagate_event(update_type=update_type, event=event, **kwargs)
2026-04-07T04:44:48.922123493Z [info]     return await wrapped()
2026-04-07T04:44:48.922132954Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.922133281Z [info]            ^^^^^^^^^^^^^^^
2026-04-07T04:44:48.922140590Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/router.py", line 161, in propagate_event
2026-04-07T04:44:48.922145745Z [info]     return await observer.wrap_outer_middleware(_wrapped, event=event, data=kwargs)
2026-04-07T04:44:48.922151302Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.922155962Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/router.py", line 153, in _wrapped
2026-04-07T04:44:48.922161073Z [info]     return await self._propagate_event(
2026-04-07T04:44:48.922165753Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.922171064Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/router.py", line 189, in _propagate_event
2026-04-07T04:44:48.922175640Z [info]     response = await router.propagate_event(update_type=update_type, event=event, **kwargs)
2026-04-07T04:44:48.925640646Z [info]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.925651997Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/router.py", line 161, in propagate_event
2026-04-07T04:44:48.925658049Z [info]     return await observer.wrap_outer_middleware(_wrapped, event=event, data=kwargs)
2026-04-07T04:44:48.925663041Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.925668322Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/router.py", line 153, in _wrapped
2026-04-07T04:44:48.925676811Z [info]     return await self._propagate_event(
2026-04-07T04:44:48.925681468Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.925687259Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/router.py", line 181, in _propagate_event
2026-04-07T04:44:48.925693138Z [info]     response = await observer.trigger(event, **kwargs)
2026-04-07T04:44:48.925698671Z [info]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.925703239Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/event/telegram.py", line 126, in trigger
2026-04-07T04:44:48.925707834Z [info]     return await wrapped_inner(event, kwargs)
2026-04-07T04:44:48.925712268Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.925716654Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/event/handler.py", line 71, in call
2026-04-07T04:44:48.925720640Z [info]     return await wrapped()
2026-04-07T04:44:48.925724446Z [info]            ^^^^^^^^^^^^^^^
2026-04-07T04:44:48.925728529Z [info]   File "/app/handlers/gamification_user_handlers.py", line 107, in daily_gift_menu
2026-04-07T04:44:48.925733326Z [info]     can_claim, time_remaining, message = gift_service.can_claim(user_id)
2026-04-07T04:44:48.929109731Z [info]                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:44:48.929116323Z [info]   File "/app/services/daily_gift_service.py", line 91, in can_claim
2026-04-07T04:44:48.929120534Z [info]     time_since_last = now - last_claim.claimed_at
2026-04-07T04:44:48.929126297Z [info]                       ~~~~^~~~~~~~~~~~~~~~~~~~~~~
2026-04-07T04:44:48.929131006Z [info] TypeError: can't subtract offset-naive and offset-aware datetimes
2026-04-07T04:44:49.746146911Z [info] 2026-04-07 04:44:49,419 - handlers.gamification_user_handlers - WARNING - No se pudo actualizar conteo en mensaje: Telegram server says - Flood control exceeded on method 'EditMessageReplyMarkup' in chat -1001966892979. Retry in 6 seconds.
2026-04-07T04:44:49.746155905Z [info] Original description: Too Many Requests: retry after 6
2026-04-07T04:44:49.746165070Z [info] (background on this error at: https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this)
2026-04-07T04:44:49.746172432Z [info] 2026-04-07 04:44:49,513 - aiogram.event - INFO - Update id=277619261 is handled. Duration 4775 ms by bot id=7360762013
2026-04-07T04:44:49.746180111Z [info] 2026-04-07 04:44:49,620 - aiogram.event - INFO - Update id=277619264 is handled. Duration 2591 ms by bot id=7360762013
2026-04-07T04:44:51.723748518Z [info] 2026-04-07 04:44:51,497 - services.besito_service - INFO - Acreditados 2 besitos a usuario 6296395093 - reaction
2026-04-07T04:44:51.723753262Z [info] 2026-04-07 04:44:51,497 - services.broadcast_service - INFO - Reacción registrada: user=6296395093, broadcast=6, besitos=2
2026-04-07T04:44:51.723758033Z [info] 2026-04-07 04:44:51,521 - services.mission_service - INFO - Mision completada: user=6296395093, mission=3
2026-04-07T04:44:51.723762641Z [info] 2026-04-07 04:44:51,551 - services.besito_service - INFO - Acreditados 5 besitos a usuario 6296395093 - mission
2026-04-07T04:44:51.723766756Z [info] 2026-04-07 04:44:51,566 - services.mission_service - INFO - Recompensa entregada: user=6296395093, reward=2
2026-04-07T04:44:51.723770990Z [info] 2026-04-07 04:44:51,589 - services.mission_service - INFO - Mision completada: user=6296395093, mission=4
2026-04-07T04:44:51.723775060Z [info] 2026-04-07 04:44:51,625 - services.besito_service - INFO - Acreditados 15 besitos a usuario 6296395093 - mission
2026-04-07T04:44:51.723779345Z [info] 2026-04-07 04:44:51,636 - services.mission_service - INFO - Recompensa entregada: user=6296395093, reward=3
2026-04-07T04:44:51.723784013Z [info] 2026-04-07 04:44:51,639 - services.broadcast_service - WARNING - Error procesando misiones para reacción: Instance <Mission at 0x7fd5d9c079d0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
2026-04-07T04:44:53.888549578Z [info] 2026-04-07 04:44:53,688 - handlers.common_handlers - INFO - /start recibido - user_id=1133183184, args=MEzKDn9p0gEU4vIZsLjMvaol2q9q4EgM, full_text='/start MEzKDn9p0gEU4vIZsLjMvaol2q9q4EgM'
2026-04-07T04:44:54.016722144Z [info] 2026-04-07 04:44:54,003 - aiogram.event - INFO - Update id=277619267 is handled. Duration 315 ms by bot id=7360762013
2026-04-07T04:44:56.777710874Z [info] 2026-04-07 04:44:56,695 - aiogram.event - INFO - Update id=277619266 is handled. Duration 5240 ms by bot id=7360762013
2026-04-07T04:44:59.830025064Z [info] 2026-04-07 04:44:59,514 - services.besito_service - INFO - Acreditados 1 besitos a usuario 6822458615 - trivia
2026-04-07T04:44:59.830033344Z [info] 2026-04-07 04:44:59,527 - services.game_service - INFO - game_service - play_trivia - 6822458615 - correct:True, streak:4
2026-04-07T04:44:59.945151088Z [info] 2026-04-07 04:44:59,943 - handlers.game_user_handlers - INFO - game_user_handlers - trivia_answer - 6822458615 - correct:True
2026-04-07T04:44:59.945157425Z [info] 2026-04-07 04:44:59,944 - aiogram.event - INFO - Update id=277619268 is handled. Duration 515 ms by bot id=7360762013
2026-04-07T04:45:00.825526103Z [info] 2026-04-07 04:45:00,656 - aiogram.event - INFO - Update id=277619269 is handled. Duration 459 ms by bot id=7360762013
2026-04-07T04:45:01.791868657Z [info] 2026-04-07 04:45:01,556 - aiogram.event - INFO - Update id=277619270 is handled. Duration 456 ms by bot id=7360762013
2026-04-07T04:45:02.780020417Z [info] 2026-04-07 04:45:02,559 - aiogram.event - INFO - Update id=277619271 is handled. Duration 475 ms by bot id=7360762013
2026-04-07T04:45:03.959318064Z [info] 2026-04-07 04:45:03,956 - services.besito_service - INFO - Acreditados 2 besitos a usuario 6296395093 - reaction
2026-04-07T04:45:03.959322924Z [info] 2026-04-07 04:45:03,956 - services.broadcast_service - INFO - Reacción registrada: user=6296395093, broadcast=6, besitos=2
2026-04-07T04:45:04.022797935Z [info] 2026-04-07 04:45:03,989 - services.mission_service - INFO - Mision completada: user=6296395093, mission=3
2026-04-07T04:45:04.095262859Z [info] 2026-04-07 04:45:04,042 - services.besito_service - INFO - Acreditados 5 besitos a usuario 6296395093 - mission
2026-04-07T04:45:04.095267681Z [info] 2026-04-07 04:45:04,066 - services.mission_service - INFO - Recompensa entregada: user=6296395093, reward=2
2026-04-07T04:45:04.139247277Z [info] 2026-04-07 04:45:04,108 - services.mission_service - INFO - Mision completada: user=6296395093, mission=4
2026-04-07T04:45:04.150337896Z [info] 2026-04-07 04:45:04,145 - services.besito_service - INFO - Acreditados 15 besitos a usuario 6296395093 - mission
2026-04-07T04:45:04.161631793Z [info] 2026-04-07 04:45:04,156 - services.mission_service - INFO - Recompensa entregada: user=6296395093, reward=3
2026-04-07T04:45:04.161635413Z [info] 2026-04-07 04:45:04,160 - services.broadcast_service - WARNING - Error procesando misiones para reacción: Instance <Mission at 0x7fd5dbf1d1d0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
2026-04-07T04:45:04.832361468Z [info] 2026-04-07 04:45:04,510 - services.game_service - INFO - game_service - get_trivia_entry_data - 6822458615 - remaining:1, streak:4
2026-04-07T04:45:04.832366604Z [info] 2026-04-07 04:45:04,676 - aiogram.event - INFO - Update id=277619272 is handled. Duration 766 ms by bot id=7360762013
2026-04-07T04:45:04.943113186Z [info] 2026-04-07 04:45:04,936 - handlers.game_user_handlers - INFO - game_user_handlers - game_trivia - 6822458615 - shown
2026-04-07T04:45:04.943119559Z [info] 2026-04-07 04:45:04,937 - aiogram.event - INFO - Update id=277619273 is handled. Duration 504 ms by bot id=7360762013
2026-04-07T04:45:06.123436694Z [info] 2026-04-07 04:45:06,113 - aiogram.event - INFO - Update id=277619274 is handled. Duration 459 ms by bot id=7360762013
2026-04-07T04:45:06.853475520Z [info] 2026-04-07 04:45:06,690 - handlers.common_handlers - INFO - /start recibido - user_id=5657439610, args=free, full_text='/start free'
2026-04-07T04:45:06.853482201Z [info] 2026-04-07 04:45:06,691 - handlers.common_handlers - INFO - Detectado args='free' para user_id=5657439610
2026-04-07T04:45:06.853487996Z [info] 2026-04-07 04:45:06,797 - handlers.common_handlers - INFO - Usuario 5657439610 membresía VIP: left
2026-04-07T04:45:06.853493689Z [info] 2026-04-07 04:45:06,806 - handlers.common_handlers - INFO - Usuario existente: True
2026-04-07T04:45:06.853499347Z [info] 2026-04-07 04:45:06,806 - handlers.common_handlers - INFO - Usuario 5657439610 ya existe, ignorando parámetro 'free'
2026-04-07T04:45:06.945913657Z [info] 2026-04-07 04:45:06,943 - services.besito_service - INFO - Acreditados 2 besitos a usuario 6296395093 - reaction
2026-04-07T04:45:06.945920562Z [info] 2026-04-07 04:45:06,943 - services.broadcast_service - INFO - Reacción registrada: user=6296395093, broadcast=6, besitos=2
2026-04-07T04:45:06.983557889Z [info] 2026-04-07 04:45:06,972 - services.mission_service - INFO - Mision completada: user=6296395093, mission=3
2026-04-07T04:45:07.021728967Z [info] 2026-04-07 04:45:07,004 - services.besito_service - INFO - Acreditados 5 besitos a usuario 6296395093 - mission
2026-04-07T04:45:07.032485703Z [info] 2026-04-07 04:45:07,026 - services.mission_service - INFO - Recompensa entregada: user=6296395093, reward=2
2026-04-07T04:45:07.054111981Z [info] 2026-04-07 04:45:07,048 - services.mission_service - INFO - Mision completada: user=6296395093, mission=4
2026-04-07T04:45:07.119382534Z [info] 2026-04-07 04:45:07,076 - services.besito_service - INFO - Acreditados 15 besitos a usuario 6296395093 - mission
2026-04-07T04:45:07.119395693Z [info] 2026-04-07 04:45:07,088 - services.mission_service - INFO - Recompensa entregada: user=6296395093, reward=3
2026-04-07T04:45:07.119402551Z [info] 2026-04-07 04:45:07,094 - services.broadcast_service - WARNING - Error procesando misiones para reacción: Instance <Mission at 0x7fd5d9a6b350> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
2026-04-07T04:45:07.162526838Z [info] 2026-04-07 04:45:07,148 - aiogram.event - INFO - Update id=277619275 is handled. Duration 457 ms by bot id=7360762013
2026-04-07T04:45:07.838050721Z [info] 2026-04-07 04:45:07,757 - aiogram.event - INFO - Update id=277619278 is handled. Duration 464 ms by bot id=7360762013
2026-04-07T04:45:07.838113137Z [info] 2026-04-07 04:45:07,599 - aiogram.event - INFO - Update id=277619277 is handled. Duration 450 ms by bot id=7360762013
2026-04-07T04:45:09.024275197Z [info] 2026-04-07 04:45:09,022 - aiogram.event - INFO - Update id=277619279 is handled. Duration 429 ms by bot id=7360762013
2026-04-07T04:45:10.778660140Z [info] 2026-04-07 04:45:10,711 - aiogram.event - INFO - Update id=277619276 is handled. Duration 3830 ms by bot id=7360762013
2026-04-07T04:45:11.166534946Z [info] 2026-04-07 04:45:11,157 - aiogram.event - INFO - Update id=277619280 is handled. Duration 901 ms by bot id=7360762013
2026-04-07T04:45:12.844365492Z [info] 2026-04-07 04:45:12,491 - aiogram.event - INFO - Update id=277619281 is not handled. Duration 20 ms by bot id=7360762013
2026-04-07T04:45:12.844370788Z [info] 2026-04-07 04:45:12,491 - aiogram.event - ERROR - Cause exception while process update id=277619281 by bot id=7360762013
2026-04-07T04:45:12.844377924Z [info] TypeError: can't subtract offset-naive and offset-aware datetimes
2026-04-07T04:45:12.844383401Z [info] Traceback (most recent call last):
2026-04-07T04:45:12.844389108Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/dispatcher.py", line 320, in _process_update
2026-04-07T04:45:12.844394395Z [info]     response = await self.feed_update(bot, update, **kwargs)
2026-04-07T04:45:12.844399593Z [info]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:45:12.844405182Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/dispatcher.py", line 164, in feed_update
2026-04-07T04:45:12.844411723Z [info]     response = await self.update.wrap_outer_middleware(
2026-04-07T04:45:12.844417291Z [info]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:45:12.844421811Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/middlewares/error.py", line 27, in __call__
2026-04-07T04:45:12.844428836Z [info]     return await handler(event, data)
2026-04-07T04:45:12.844434060Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:45:12.844438884Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/middlewares/user_context.py", line 58, in __call__
2026-04-07T04:45:12.844444398Z [info]     return await handler(event, data)
2026-04-07T04:45:12.844450082Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:45:12.844456147Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/fsm/middleware.py", line 43, in __call__
2026-04-07T04:45:12.844461465Z [info]     return await handler(event, data)
2026-04-07T04:45:12.848746699Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-04-07T04:45:12.848755571Z [info]   File "/opt/venv/lib/python3.11/site-packages/aiogram/dispatcher/event/telegram.py", line 126, in trigger
2026-04-07T04:45:12.848761440Z [info]     return await wrapped_inner(event, kwargs)
2026-04-07T04:45:12.848767091Z [info]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

