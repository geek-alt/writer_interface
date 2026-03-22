import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref(null)
  const status = ref('disconnected')
  const _listeners = []
  let _pingInterval = null

  function connect(projectId) {
    if (socket.value?.readyState === WebSocket.OPEN) return
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    socket.value = new WebSocket(`${proto}://${location.host}/ws/generate/${projectId}`)
    status.value = 'connecting'

    socket.value.onopen = () => {
      status.value = 'connected'
      _pingInterval = setInterval(() => {
        if (socket.value?.readyState === WebSocket.OPEN) {
          socket.value.send(JSON.stringify({ action: 'ping' }))
        }
      }, 30000)
    }

    socket.value.onclose = () => {
      status.value = 'disconnected'
      clearInterval(_pingInterval)
    }
    socket.value.onerror = () => {
      status.value = 'error'
    }
    socket.value.onmessage = event => {
      try {
        const data = JSON.parse(event.data)
        _listeners.forEach(fn => fn(data))
      } catch {
        // ignore malformed messages
      }
    }
  }

  function send(data) {
    if (socket.value?.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(data))
    }
  }

  function onMessage(fn) {
    _listeners.push(fn)
    return () => {
      const i = _listeners.indexOf(fn)
      if (i > -1) _listeners.splice(i, 1)
    }
  }

  function disconnect() {
    clearInterval(_pingInterval)
    socket.value?.close()
    socket.value = null
    status.value = 'disconnected'
  }

  return { status, connect, send, onMessage, disconnect }
})
