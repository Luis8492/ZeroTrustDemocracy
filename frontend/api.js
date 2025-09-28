const API_BASE = (import.meta?.env?.VITE_API_BASE) ?? window.location.origin;

function buildApiUrl(path) {
  return new URL(path, API_BASE).toString();
}

export async function fetchNextQA(evaledIds = [], municipality) {
  const res = await fetch(buildApiUrl(`/api/qa/next?municipality=${municipality}`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      evaled_ids: evaledIds
    })
  });
  if (!res.ok) {
    throw new Error(`API呼び出しに失敗しました: ${res.status}`);
  }
  const data = await res.json();
  return data;
}

export async function fetchMetaData(evaledIds = [], municipality) {
  const res = await fetch(buildApiUrl(`/api/qa/meta?municipality=${municipality}`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      evaled_ids: evaledIds
    })
  });
  if (!res.ok) {
    throw new Error(`API呼び出しに失敗しました: ${res.status}`);
  }
  const data = await res.json();
  return data;
}
