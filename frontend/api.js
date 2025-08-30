export async function fetchNextQA(evaledIds = [], municipality = "default") {
  const url = `http://localhost:8000/api/qa/next?municipality=${encodeURIComponent(municipality)}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      evaled_ids: evaledIds,
      municipality
    })
  });
  if (!res.ok) {
    throw new Error(`API呼び出しに失敗しました: ${res.status}`);
  }
  const data = await res.json();
  return data;
}

export async function fetchMetaData(evaledIds = [], municipality = "default") {
  const url = `http://localhost:8000/api/qa/meta?municipality=${encodeURIComponent(municipality)}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      evaled_ids: evaledIds,
      municipality
    })
  });
  if (!res.ok) {
    throw new Error(`API呼び出しに失敗しました: ${res.status}`);
  }
  const data = await res.json();
  return data;
}
