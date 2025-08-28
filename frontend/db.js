// db.js
export async function getDB() {
  return idb.openDB("EvalDB", 1, {
    upgrade(db) {
      db.createObjectStore("evaluations", { keyPath: "QA_id" });
    },
  });
}

export async function saveEvaluation(evaluation) {//{QA_id,eval}
  const db = await getDB();
  const tx = db.transaction('evaluations','readwrite');
  const evalDB = tx.objectStore('evaluations');
  await evalDB.put(evaluation);
  await tx.done;
}

export async function listEvaluatedIDs() {
  const db = await getDB();
  const tx = db.transaction('evaluations','readwrite');
  const evalDB = tx.objectStore('evaluations');
  const evalDBContent = await evalDB.getAll();
  //let evaledIds = []
  //evalDBContent.forEach(element => {
  //  evaledIds.push(element.id);
  //});
  //return evaledIds;
  return evalDBContent.map(e => e.QA_id);
}

export async function listEvaluations() {
  const db = await getDB();
  const tx = db.transaction('evaluations','readonly');
  const evalDB = tx.objectStore('evaluations');
  const evalDBContent = await evalDB.getAll();
  return evalDBContent;
}
