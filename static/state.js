/**
 * 上古必斩必杀 状态管理
 */

let threadId = null;
let busy = false;
let pendingMessages = [];
let todoPollInterval = null;
let currentAbortController = null;
let alertEventSource = null;

function getThreadId() {
  return threadId;
}

function setThreadId(id) {
  threadId = id;
}

function isBusy() {
  return busy;
}

function setBusy(value) {
  busy = value;
}

function getPendingMessages() {
  return pendingMessages;
}

function addPendingMessage(msg) {
  pendingMessages.push(msg);
}

function clearPendingMessages() {
  pendingMessages = [];
}

function setTodoPollInterval(interval) {
  todoPollInterval = interval;
}

function getTodoPollInterval() {
  return todoPollInterval;
}

function setCurrentAbortController(ctrl) {
  currentAbortController = ctrl;
}

function getCurrentAbortController() {
  return currentAbortController;
}

function setAlertEventSource(source) {
  alertEventSource = source;
}

function getAlertEventSource() {
  return alertEventSource;
}