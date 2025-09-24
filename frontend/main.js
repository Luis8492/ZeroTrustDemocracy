import { fetchNextQA, fetchMetaData } from './api.js';
import { listEvaluatedIDs, saveEvaluation } from './db.js'; // IndexedDB 側から取得

const MUNICIPALITY = "Tokyo";

var qa_id;

function resetEvaluation() {
  const defaultRadio = document.querySelector('input[name="eval"][value="0"]');
  if (defaultRadio) {
    defaultRadio.checked = true;
  }
}

function formatSpeech(QA){
  let speechView = "";
  for (let speech of QA){
    speechView += speech.mark+" "+speech.role+" "+speech.comment+"\n";
  }
  return speechView;
}

async function fetchQuestion(){
  // 既に評価済みのQAのIDをIndexedDBから取得
  const evaledIds = await listEvaluatedIDs();
  const qa = await fetchNextQA(evaledIds, MUNICIPALITY);
  if (qa.QA) {
    qa_id = qa.id;
    document.querySelector("#meetingName").innerText = qa.committee_name;
    document.querySelector("#meetingDate").innerText = qa.committee_date;
    document.querySelector("#topic_intro").innerText = formatSpeech(qa.topic_intro);
    document.querySelector("#question").innerText = formatSpeech(qa.QA);
    document.querySelector('#debugSection').innerText = JSON.stringify(qa,"",4)
  } else {
    document.querySelector("#question").innerText = "noNONO";
    // 他の要素（topic_introや名前など）も表示に追加可能
  }
  resetEvaluation();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function recordEval() {
  const selected = document.querySelector('input[name="eval"]:checked');
  if (!selected) {
    alert("評価を選んでください。");
    return;
  }
  const evalValue = parseInt(selected.value);
  saveEvaluation({"QA_id":qa_id,"eval":evalValue});
  fetchQuestion();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}


document.addEventListener("DOMContentLoaded", fetchQuestion);

window.recordEval = recordEval;
window.fetchQuestion = fetchQuestion;
window.fetchNextQA = (ids) => fetchNextQA(ids, MUNICIPALITY);
window.listEvaluatedIDs = listEvaluatedIDs;
window.fetchMetaData = (ids) => fetchMetaData(ids, MUNICIPALITY);
window.scrollToTop = scrollToTop;
