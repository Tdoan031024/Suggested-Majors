import { useState, useEffect } from 'react'
import { fetchGroups } from '../api/client'

/**
 * Fetches the 9 nhóm ngành from the API.
 * Returns { groups: [{ten_nhom, so_nganh, nganh}], loading, error }
 */
export function useGroups() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchGroups()
      .then(r => setGroups(r.data.groups))
      .catch(e => setError('Không kết nối được API. Hãy chắc chắn backend đang chạy.'))
      .finally(() => setLoading(false))
  }, [])

  return { groups, loading, error }
}
