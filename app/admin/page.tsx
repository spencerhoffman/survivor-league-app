'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { User, GameSettings } from '@/types'

export default function AdminPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [gameSettings, setGameSettings] = useState<GameSettings | null>(null)
  const [teams, setTeams] = useState<string[]>([])
  const [recordForm, setRecordForm] = useState({ team: '', outcome: 'win' })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (!token || !userData) {
      router.push('/login')
      return
    }

    const parsedUser = JSON.parse(userData)
    if (parsedUser.role !== 'admin') {
      router.push('/dashboard')
      return
    }

    setUser(parsedUser)
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
      const [settingsRes, teamsRes] = await Promise.all([
        fetch('/api/admin/settings'),
        fetch('/api/teams')
      ])

      if (settingsRes?.ok) {
        const settingsData = await settingsRes.json()
        setGameSettings(settingsData)
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

  const advanceWeek = async () => {
    try {
      const response = await apiCall('/api/admin/advance-week', { method: 'POST' })
      if (response?.ok) {
        fetchData()
        alert('Week advanced successfully')
      }
    } catch (error) {
      console.error('Error advancing week:', error)
    }
  }

  const lockPicks = async () => {
    try {
      const response = await apiCall('/api/admin/lock-picks', { method: 'POST' })
      if (response?.ok) {
        fetchData()
        alert('Picks locked successfully')
      }
    } catch (error) {
      console.error('Error locking picks:', error)
    }
  }

  const unlockPicks = async () => {
    try {
      const response = await apiCall('/api/admin/unlock-picks', { method: 'POST' })
      if (response?.ok) {
        fetchData()
        alert('Picks unlocked successfully')
      }
    } catch (error) {
      console.error('Error unlocking picks:', error)
    }
  }

  const processWeekResults = async () => {
    try {
      const response = await apiCall('/api/admin/process-week-results', { method: 'POST' })
      if (response?.ok) {
        const data = await response.json()
        alert(`Week results processed: ${data.total_eliminated} eliminated, ${data.total_surviving} surviving`)
        fetchData()
      }
    } catch (error) {
      console.error('Error processing week results:', error)
    }
  }

  const recordResult = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await apiCall('/api/admin/record-result', {
        method: 'POST',
        body: JSON.stringify(recordForm)
      })
      if (response?.ok) {
        alert('Game result recorded successfully')
        setRecordForm({ team: '', outcome: 'win' })
      }
    } catch (error) {
      console.error('Error recording result:', error)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
            <div className="flex items-center space-x-4">
              <Button onClick={() => router.push('/dashboard')} variant="outline">
                Back to Dashboard
              </Button>
              <Button onClick={() => {
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                router.push('/login')
              }} variant="outline">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <Tabs defaultValue="game-control" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="game-control">Game Control</TabsTrigger>
              <TabsTrigger value="results">Record Results</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>

            <TabsContent value="game-control" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Week Management</CardTitle>
                  <CardDescription>
                    Current Week: {gameSettings?.current_week} | 
                    Picks {gameSettings?.picks_locked ? 'LOCKED' : 'OPEN'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex space-x-2">
                    <Button onClick={advanceWeek}>Advance Week</Button>
                    <Button 
                      onClick={gameSettings?.picks_locked ? unlockPicks : lockPicks}
                      variant="outline"
                    >
                      {gameSettings?.picks_locked ? 'Unlock Picks' : 'Lock Picks'}
                    </Button>
                  </div>
                  <Button onClick={processWeekResults} variant="destructive">
                    Process Week Results
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="results" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Record Game Results</CardTitle>
                  <CardDescription>Record wins/losses for teams this week</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={recordResult} className="space-y-4">
                    <div>
                      <Label htmlFor="team">Team</Label>
                      <select
                        id="team"
                        value={recordForm.team}
                        onChange={(e) => setRecordForm({ ...recordForm, team: e.target.value })}
                        className="w-full p-2 border rounded"
                        required
                      >
                        <option value="">Select Team</option>
                        {teams.map((team) => (
                          <option key={team} value={team}>{team}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="outcome">Outcome</Label>
                      <select
                        id="outcome"
                        value={recordForm.outcome}
                        onChange={(e) => setRecordForm({ ...recordForm, outcome: e.target.value })}
                        className="w-full p-2 border rounded"
                        required
                      >
                        <option value="win">Win</option>
                        <option value="loss">Loss</option>
                        <option value="bye">Bye</option>
                      </select>
                    </div>
                    <Button type="submit">Record Result</Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="settings" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Game Settings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label>Entry Fee: ${gameSettings?.entry_fee}</Label>
                    </div>
                    <div>
                      <Label>Buyback Multiplier: {gameSettings?.buyback_multiplier}x</Label>
                    </div>
                    <div>
                      <Label>Current Week: {gameSettings?.current_week}</Label>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}
