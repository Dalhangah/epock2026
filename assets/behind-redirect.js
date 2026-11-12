/* Preserve prior links while moving AI-specific records to their own page. */
(() => { const moved = new Set(['form','proportion','rules','render-test','detail-6']); const id = location.hash.slice(1); if (moved.has(id)) location.replace('ai-records.html' + location.hash); })();
