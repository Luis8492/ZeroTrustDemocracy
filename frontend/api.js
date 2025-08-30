export async function fetchNextQA(evaledIds = [], municipality) {
  const res = await fetch(
    `http://localhost:8000/api/qa/next?municipality=${encodeURIComponent(
      municipality
    )}`,
    {
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
  const res = await fetch(
    `http://localhost:8000/api/qa/meta?municipality=${encodeURIComponent(
      municipality
    )}`,
    {
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
