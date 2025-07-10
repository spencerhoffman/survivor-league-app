'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { User, Player, GameSettings, LeaderboardEntry } from '@/types'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [players, setPlayers] = useState<Player[]>([])
  const [gameSettings, setGameSettings] = useState<GameSettings | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [teams, setTeams] = useState<string[]>([])
  const [newPlayerName, setNewPlayerName] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (!token || !userData) {
      router.push('/login')
      return
    }

    setUser(JSON.parse(userData))
    fetchData()
  }, [router])

  const apiCall = async (url: string, options: RequestInit = {}) => {
    const token = localStorage.getItem('token')
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
      return null
    }

    return response
  }

  const fetchData = async () => {
    try {
      const [playersRes, settingsRes, leaderboardRes, teamsRes] = await Promise.all([
        apiCall('/api/players/me'),
        fetch('/api/admin/settings'),
        fetch('/api/leaderboard'),
        fetch('/api/teams')
      ])

      if (playersRes?.ok) {
        const playersData = await playersRes.json()
        setPlayers(playersData)
      }

      if (settingsRes?.ok) {
        const settingsData = await settingsRes.json()
        setGameSettings(settingsData)
      }

      if (leaderboardRes?.ok) {
        const leaderboardData = await leaderboardRes.json()
        setLeaderboard(leaderboardData)
      }

      if (teamsRes?.ok) {
        const teamsData = await teamsRes.json()
        setTeams(teamsData)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const createPlayer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPlayerName.trim()) return

    try {
      const response = await apiCall('/api/players', {
        method: 'POST',
        body: JSON.stringify({ entry_name: newPlayerName })
      })

      if (response?.ok) {
        setNewPlayerName('')
        fetchData()
      }
    } catch (error) {
      console.error('Error creating player:', error)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      eliminated: 'bg-red-100 text-red-800',
      redemption: 'bg-yellow-100 text-yellow-800'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">Survivor League</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Welcome, {user?.username}</span>
              {user?.role === 'admin' && (
                <Button onClick={() => router.push('/admin')} variant="outline">
                  Admin Panel
                </Button>
              )}
              <Button onClick={logout} variant="outline">Logout</Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <Tabs defaultValue="players" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="players">My Players</TabsTrigger>
              <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
              <TabsTrigger value="picks">Make Picks</TabsTrigger>
            </TabsList>

            <TabsContent value="players" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Create New Player Entry</CardTitle>
                  <CardDescription>
                    Entry Fee: ${gameSettings?.entry_fee} | Current Week: {gameSettings?.current_week}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={createPlayer} className="flex space-x-2">
                    <Input
                      placeholder="Enter player name"
                      value={newPlayerName}
                      onChange={(e) => setNewPlayerName(e.target.value)}
                      required
                    />
                    <Button type="submit">Create Player</Button>
                  </form>
                </CardContent>
              </Card>

              <div className="grid gap-4">
                {players.map((player) => (
                  <Card key={player.id}>
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-lg font-semibold">{player.entry_name}</h3>
                          <p className="text-sm text-gray-500">
                            Weeks Survived: {player.weeks_survived} | 
                            Buybacks: {player.buybacks} | 
                            Contribution: ${player.financial_contribution}
                          </p>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(player.status)}`}>
                          {player.status}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="leaderboard" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>League Standings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {leaderboard.map((entry, index) => (
                      <div key={entry.player_id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <div className="flex items-center space-x-3">
                          <span className="font-bold text-lg">#{index + 1}</span>
                          <div>
                            <p className="font-medium">{entry.entry_name}</p>
                            <p className="text-sm text-gray-500">@{entry.username}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{entry.weeks_survived} weeks</p>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(entry.status)}`}>
                            {entry.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="picks" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Weekly Picks</CardTitle>
                  <CardDescription>
                    Week {gameSettings?.current_week} | 
                    Picks {gameSettings?.picks_locked ? 'LOCKED' : 'OPEN'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {gameSettings?.picks_locked ? (
                    <p className="text-center text-gray-500 py-8">
                      Picks are currently locked for this week.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {players.filter(p => p.status === 'active').map((player) => (
                        <div key={player.id} className="border rounded p-4">
                          <h4 className="font-medium mb-2">{player.entry_name}</h4>
                          <div className="grid grid-cols-2 gap-2">
                            {teams.slice(0, 8).map((team) => (
                              <Button key={team} variant="outline" size="sm">
                                {team}
                              </Button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}
