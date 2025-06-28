import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Trophy, Users, Calendar, Settings, LogOut, Plus, AlertCircle } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'https://app-xieyxwel.fly.dev'

interface User {
  id: string
  username: string
  role: 'admin' | 'player'
}

interface Player {
  id: string
  user_id: string
  entry_name: string
  status: 'active' | 'eliminated' | 'redemption'
  eliminated_week?: number
  redemption_visits: number
  buybacks: number
  entry_fee_paid: boolean
}


interface LeaderboardEntry {
  player_id: string
  entry_name: string
  username: string
  status: string
  weeks_survived: number
  redemption_visits: number
  buybacks: number
  eliminated_week?: number
  financial_contribution: number
}

interface GameSettings {
  current_week: number
  entry_fee: number
  buyback_multiplier: number
  picks_locked: boolean
}

interface GameResult {
  id: string
  week: number
  team: string
  outcome: string
  created_at: string
}

interface WeeklyPick {
  id: string
  player_id: string
  week: number
  team: string
  is_redemption: boolean
  is_underdog: boolean
  created_at: string
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [myPlayers, setMyPlayers] = useState<Player[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [teams, setTeams] = useState<string[]>([])
  const [gameSettings, setGameSettings] = useState<GameSettings | null>(null)
  const [underdogTeams, setUnderdogTeams] = useState<string[]>([])
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)

  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '' })
  const [resetPasswordForm, setResetPasswordForm] = useState({ username: '', email: '', newPassword: '' })
  const [showResetPassword, setShowResetPassword] = useState(false)
  const [newPlayerName, setNewPlayerName] = useState('')
  const [selectedTeam, setSelectedTeam] = useState('')
  const [selectedPlayer, setSelectedPlayer] = useState('')
  const [gameResults, setGameResults] = useState<GameResult[]>([])
  const [teamResults, setTeamResults] = useState<Record<string, 'win' | 'loss' | 'bye' | null>>({})
  const [underdogTeamSelections, setUnderdogTeamSelections] = useState<Record<string, boolean>>({})
  const [redemptionPicks, setRedemptionPicks] = useState({ underdogTeam1: '', underdogTeam2: '' })
  const [currentPicks, setCurrentPicks] = useState<WeeklyPick[]>([])
  const [editingPick, setEditingPick] = useState<string | null>(null)

  useEffect(() => {
    if (token) {
      fetchUserProfile()
      fetchUserData()
      fetchTeams()
      fetchGameSettings()
      fetchLeaderboard()
    } else {
      setInitializing(false)
    }
  }, [token])

  useEffect(() => {
    if (user?.role === 'admin' && gameSettings?.current_week) {
      fetchUnderdogTeams(gameSettings.current_week)
      fetchGameResults()
    }
  }, [user, gameSettings?.current_week])

  useEffect(() => {
    if (selectedPlayer) {
      fetchCurrentPicks(selectedPlayer)
    } else {
      setCurrentPicks([])
    }
  }, [selectedPlayer])

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (options.headers) {
      Object.assign(headers, options.headers)
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || 'Request failed')
    }

    return response.json()
  }

  const fetchUserProfile = async () => {
    try {
      const userData = await apiCall('/me')
      setUser(userData)
    } catch (err) {
      console.error('Failed to fetch user profile:', err)
      logout()
    } finally {
      setInitializing(false)
    }
  }

  const fetchUserData = async () => {
    try {
      const playersData = await apiCall('/players/me')
      setMyPlayers(playersData)
    } catch (err) {
      console.error('Failed to fetch user data:', err)
      logout()
    }
  }

  const fetchTeams = async () => {
    try {
      const teamsData = await apiCall('/teams')
      setTeams(teamsData)
    } catch (err) {
      console.error('Failed to fetch teams:', err)
    }
  }

  const fetchGameSettings = async () => {
    try {
      const settings = await apiCall('/admin/settings')
      setGameSettings(settings)
      if (settings.current_week) {
        fetchUnderdogTeams(settings.current_week)
      }
    } catch (err) {
      console.error('Failed to fetch game settings:', err)
    }
  }

  const fetchLeaderboard = async () => {
    try {
      const leaderboardData = await apiCall('/leaderboard')
      setLeaderboard(leaderboardData)
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err)
    }
  }

  const fetchUnderdogTeams = async (week: number) => {
    try {
      const underdogs = await apiCall(`/admin/underdog-teams/${week}`)
      setUnderdogTeams(underdogs)
    } catch (err) {
      console.error('Failed to fetch underdog teams:', err)
    }
  }

  const login = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await apiCall('/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      })

      setToken(response.token)
      setUser(response.user)
      localStorage.setItem('token', response.token)
      setSuccess('Logged in successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const register = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await apiCall('/auth/register', {
        method: 'POST',
        body: JSON.stringify(registerForm),
      })

      setToken(response.token)
      setUser(response.user)
      localStorage.setItem('token', response.token)
      setSuccess('Registered successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
    setMyPlayers([])
    setLeaderboard([])
  }

  const resetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!resetPasswordForm.username || !resetPasswordForm.email || !resetPasswordForm.newPassword) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      await apiCall('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({
          username: resetPasswordForm.username,
          email: resetPasswordForm.email,
          new_password: resetPasswordForm.newPassword
        })
      })
      setSuccess('Password reset successfully! You can now login with your new password.')
      setShowResetPassword(false)
      setResetPasswordForm({ username: '', email: '', newPassword: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Password reset failed')
    } finally {
      setLoading(false)
    }
  }

  const createPlayer = async () => {
    if (!newPlayerName.trim()) return

    setLoading(true)
    setError('')

    try {
      await apiCall('/players', {
        method: 'POST',
        body: JSON.stringify({ entry_name: newPlayerName }),
      })

      setNewPlayerName('')
      setSuccess('Player entry created successfully!')
      fetchUserData()
      fetchLeaderboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create player')
    } finally {
      setLoading(false)
    }
  }

  const makePick = async () => {
    if (!selectedPlayer || !selectedTeam) return

    setLoading(true)
    setError('')

    try {
      await apiCall(`/players/${selectedPlayer}/picks`, {
        method: 'POST',
        body: JSON.stringify({ team: selectedTeam }),
      })

      setSelectedTeam('')
      setSuccess('Pick submitted successfully!')
      fetchCurrentPicks(selectedPlayer)
      fetchUserData()
      fetchLeaderboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit pick')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500">Active</Badge>
      case 'eliminated':
        return <Badge className="bg-red-500">Eliminated</Badge>
      case 'redemption':
        return <Badge className="bg-yellow-500">Redemption</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const fetchGameResults = async () => {
    try {
      const response = await apiCall(`/admin/game-results/${gameSettings?.current_week || 1}`)
      setGameResults(response)
    } catch (err) {
      console.error('Failed to fetch game results:', err)
    }
  }




  const recordTableGameResults = async () => {
    const teamsWithOutcomes = Object.entries(teamResults).filter(([_, outcome]) => outcome !== null)
    
    if (teamsWithOutcomes.length === 0) {
      setError('Please select an outcome for at least one team')
      return
    }

    setLoading(true)
    try {
      for (const [team, outcome] of teamsWithOutcomes) {
        await apiCall('/admin/record-result', {
          method: 'POST',
          body: JSON.stringify({
            team: team,
            outcome: outcome
          })
        })
      }
      setSuccess('Game results recorded successfully')
      setTeamResults({})
      fetchGameResults()
    } catch (err: any) {
      setError(err.message || 'Failed to record game results')
    } finally {
      setLoading(false)
    }
  }

  const saveUnderdogTeams = async () => {
    const selectedUnderdogs = Object.entries(underdogTeamSelections)
      .filter(([_, selected]) => selected)
      .map(([team, _]) => team)

    if (selectedUnderdogs.length === 0) {
      setError('Please select at least one underdog team')
      return
    }

    setLoading(true)
    try {
      for (const team of selectedUnderdogs) {
        await apiCall('/admin/underdog-teams', {
          method: 'POST',
          body: JSON.stringify({ team, week: gameSettings?.current_week })
        })
      }
      setSuccess('Underdog teams saved successfully')
      setUnderdogTeamSelections({})
      fetchUnderdogTeams(gameSettings?.current_week || 1)
    } catch (err: any) {
      setError(err.message || 'Failed to save underdog teams')
    } finally {
      setLoading(false)
    }
  }

  const resetLeague = async () => {
    if (!confirm('Are you sure you want to reset the entire league? This will delete ALL players, picks, results, and non-admin users. This action cannot be undone.')) {
      return
    }

    setLoading(true)
    try {
      await apiCall('/admin/reset-league', {
        method: 'POST'
      })
      setSuccess('League reset successfully! All data has been cleared.')
      
      setMyPlayers([])
      setLeaderboard([])
      setGameResults([])
      setUnderdogTeams([])
      setTeamResults({})
      setCurrentPicks([])
      setSelectedPlayer('')
      
      fetchGameSettings()
      fetchLeaderboard()
    } catch (err: any) {
      setError(err.message || 'Failed to reset league')
    } finally {
      setLoading(false)
    }
  }

  const lockPicksAndAdvanceWeek = async () => {
    if (!confirm('Are you sure you want to process week results, lock picks, and advance to the next week? This will eliminate players who picked losing teams and prevent further pick changes for the current week.')) {
      return
    }

    setLoading(true)
    try {
      const processResult = await apiCall('/admin/process-week-results', {
        method: 'POST'
      })
      
      await apiCall('/admin/lock-picks', {
        method: 'POST'
      })
      await apiCall('/admin/advance-week', {
        method: 'POST'
      })
      
      setSuccess(`Week processed successfully! ${processResult.total_eliminated} players eliminated. Picks locked and advanced to next week.`)
      
      await fetchGameSettings()
      await fetchLeaderboard()
      await fetchUnderdogTeams((gameSettings?.current_week || 1) + 1)
      await fetchGameResults()
    } catch (err: any) {
      setError(err.message || 'Failed to process week results and advance week')
    } finally {
      setLoading(false)
    }
  }

  const unlockPicksAndReturnToPreviousWeek = async () => {
    if (!confirm('Are you sure you want to unlock picks and return to the previous week? This will allow pick changes again.')) {
      return
    }

    setLoading(true)
    try {
      await apiCall('/admin/unlock-picks', {
        method: 'POST'
      })
      
      const currentWeek = gameSettings?.current_week || 1
      if (currentWeek > 1) {
        const newWeek = currentWeek - 1
        setSuccess(`Picks unlocked and returned to week ${newWeek}. Note: Week decrement requires manual backend adjustment to week ${newWeek}.`)
      } else {
        setSuccess('Picks unlocked. Already at week 1, cannot go to previous week.')
      }
      
      await fetchGameSettings()
      await fetchUnderdogTeams(gameSettings?.current_week || 1)
      await fetchGameResults()
    } catch (err: any) {
      setError(err.message || 'Failed to unlock picks and return to previous week')
    } finally {
      setLoading(false)
    }
  }

  const makeRedemptionPicks = async () => {
    if (!selectedPlayer || !redemptionPicks.underdogTeam1 || !redemptionPicks.underdogTeam2) {
      setError('Please select both underdog teams for redemption round')
      return
    }

    if (redemptionPicks.underdogTeam1 === redemptionPicks.underdogTeam2) {
      setError('Please select two different underdog teams')
      return
    }

    setLoading(true)
    try {
      await apiCall(`/players/${selectedPlayer}/redemption-picks`, {
        method: 'POST',
        body: JSON.stringify({
          underdog_team1: redemptionPicks.underdogTeam1,
          underdog_team2: redemptionPicks.underdogTeam2
        })
      })
      setSuccess('Redemption picks submitted successfully!')
      setRedemptionPicks({ underdogTeam1: '', underdogTeam2: '' })
      setSelectedPlayer('')
      fetchCurrentPicks(selectedPlayer)
      fetchLeaderboard()
    } catch (err: any) {
      setError(err.message || 'Failed to submit redemption picks')
    } finally {
      setLoading(false)
    }
  }

  const getAvailableTeams = (_playerId: string): string[] => {
    return teams
  }

  const fetchCurrentPicks = async (playerId: string) => {
    if (!playerId) {
      setCurrentPicks([])
      return
    }
    
    try {
      const picks = await apiCall(`/players/${playerId}/picks/current-week`)
      setCurrentPicks(picks)
    } catch (err) {
      console.error('Failed to fetch current picks:', err)
      setCurrentPicks([])
    }
  }

  const updatePick = async (pickId: string, team: string, isUnderdog: boolean = false) => {
    if (!selectedPlayer) return

    setLoading(true)
    setError('')

    try {
      await apiCall(`/players/${selectedPlayer}/picks/${pickId}`, {
        method: 'PUT',
        body: JSON.stringify({ team, is_underdog: isUnderdog }),
      })

      setSuccess('Pick updated successfully!')
      setEditingPick(null)
      fetchCurrentPicks(selectedPlayer)
      fetchUserData()
      fetchLeaderboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pick')
    } finally {
      setLoading(false)
    }
  }

  const deletePick = async (pickId: string) => {
    if (!selectedPlayer) return

    setLoading(true)
    setError('')

    try {
      await apiCall(`/players/${selectedPlayer}/picks/${pickId}`, {
        method: 'DELETE',
      })

      setSuccess('Pick deleted successfully!')
      fetchCurrentPicks(selectedPlayer)
      fetchUserData()
      fetchLeaderboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete pick')
    } finally {
      setLoading(false)
    }
  }

  const handleBuyback = async (playerId: string) => {
    if (!gameSettings) return
    
    try {
      setLoading(true)
      setError('')
      await apiCall(`/players/${playerId}/buyback`, {
        method: 'POST',
        body: JSON.stringify({
          week: gameSettings.current_week
        })
      })
      setSuccess('Buyback successful!')
      fetchLeaderboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process buyback')
    } finally {
      setLoading(false)
    }
  }

  const handleUndo = async (playerId: string) => {
    if (!gameSettings) return
    
    try {
      setLoading(true)
      setError('')
      await apiCall(`/players/${playerId}/undo`, {
        method: 'POST',
        body: JSON.stringify({
          week: gameSettings.current_week
        })
      })
      setSuccess('Undo contribution successful!')
      fetchLeaderboard()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process undo')
    } finally {
      setLoading(false)
    }
  }

  if (initializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-lg font-medium text-gray-900">Loading...</div>
        </div>
      </div>
    )
  }

  if (!token || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-900">Survivor League</CardTitle>
            <CardDescription>Welcome to the NFL Survivor League</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="register">Register</TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                {!showResetPassword ? (
                  <div className="space-y-4">
                    <form onSubmit={login} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input
                          id="username"
                          type="text"
                          value={loginForm.username}
                          onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="password">Password</Label>
                        <Input
                          id="password"
                          type="password"
                          value={loginForm.password}
                          onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                      </Button>
                    </form>
                    <div className="text-center">
                      <Button 
                        variant="link" 
                        onClick={() => setShowResetPassword(true)}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        Forgot Password?
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="text-center">
                      <h3 className="text-lg font-semibold">Reset Password</h3>
                      <p className="text-sm text-gray-600">Enter your username, email, and new password</p>
                    </div>
                    <form onSubmit={resetPassword} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="reset-username">Username</Label>
                        <Input
                          id="reset-username"
                          type="text"
                          value={resetPasswordForm.username}
                          onChange={(e) => setResetPasswordForm({ ...resetPasswordForm, username: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="reset-email">Email</Label>
                        <Input
                          id="reset-email"
                          type="email"
                          value={resetPasswordForm.email}
                          onChange={(e) => setResetPasswordForm({ ...resetPasswordForm, email: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="reset-new-password">New Password</Label>
                        <Input
                          id="reset-new-password"
                          type="password"
                          value={resetPasswordForm.newPassword}
                          onChange={(e) => setResetPasswordForm({ ...resetPasswordForm, newPassword: e.target.value })}
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? 'Resetting Password...' : 'Reset Password'}
                      </Button>
                    </form>
                    <div className="text-center">
                      <Button 
                        variant="link" 
                        onClick={() => setShowResetPassword(false)}
                        className="text-sm text-gray-600 hover:text-gray-800"
                      >
                        Back to Login
                      </Button>
                    </div>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="register">
                <form onSubmit={register} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reg-username">Username</Label>
                    <Input
                      id="reg-username"
                      type="text"
                      value={registerForm.username}
                      onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-password">Password</Label>
                    <Input
                      id="reg-password"
                      type="password"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? 'Registering...' : 'Register'}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            {error && (
              <Alert className="mt-4 border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="mt-4 border-green-200 bg-green-50">
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Trophy className="h-8 w-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Survivor League</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user.username}</span>
              {user.role === 'admin' && (
                <Badge className="bg-purple-500">Admin</Badge>
              )}
              <Button variant="outline" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="picks">Make Picks</TabsTrigger>
            <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
            <TabsTrigger value="pot-tracker">Pot Tracker</TabsTrigger>
            {user.role === 'admin' && <TabsTrigger value="admin">Admin</TabsTrigger>}
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Calendar className="h-5 w-5" />
                    <span>Current Week</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">
                    {gameSettings?.current_week || 1}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Picks {gameSettings?.picks_locked ? 'Locked' : 'Open'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="h-5 w-5" />
                    <span>My Entries</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">
                    {myPlayers.length}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Active entries in the league
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Entry Fee</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-purple-600">
                    ${gameSettings?.entry_fee || 35}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Per entry
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>My Players</CardTitle>
                <CardDescription>Manage your survivor league entries</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Entry name (e.g., John 1, John 2)"
                      value={newPlayerName}
                      onChange={(e) => setNewPlayerName(e.target.value)}
                    />
                    <Button onClick={createPlayer} disabled={loading}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Entry
                    </Button>
                  </div>

                  <div className="space-y-2">
                    {myPlayers.map((player) => (
                      <div key={player.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <span className="font-medium">{player.entry_name}</span>
                          {getStatusBadge(player.status)}
                        </div>
                        <div className="text-sm text-gray-600">
                          Redemptions: {player.redemption_visits} | Buybacks: {player.buybacks}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="picks" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Make Your Pick - Week {gameSettings?.current_week}</CardTitle>
                <CardDescription>
                  {gameSettings?.picks_locked 
                    ? 'Picks are currently locked' 
                    : 'Select a team you think will win this week'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Select Player Entry</Label>
                    <Select value={selectedPlayer} onValueChange={setSelectedPlayer}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose your entry" />
                      </SelectTrigger>
                      <SelectContent>
                        {myPlayers.filter(p => p.status === 'active' || p.status === 'redemption').map((player) => (
                          <SelectItem key={player.id} value={player.id}>
                            {player.entry_name} {player.status === 'redemption' && '(Redemption Round)'}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedPlayer && currentPicks.length > 0 && (
                    <div className="space-y-4">
                      <div className="border rounded-lg p-4 bg-gray-50">
                        <h4 className="font-medium mb-3">Current Picks for Week {gameSettings?.current_week}</h4>
                        <div className="space-y-2">
                          {currentPicks.map((pick) => (
                            <div key={pick.id} className="flex items-center justify-between p-3 border rounded-lg bg-white">
                              <div className="flex items-center space-x-3">
                                <span className="font-medium">{pick.team}</span>
                                {pick.is_redemption && <Badge variant="outline">Redemption</Badge>}
                                {pick.is_underdog && <Badge variant="secondary">Underdog</Badge>}
                              </div>
                              {!gameSettings?.picks_locked && (
                                <div className="flex space-x-2">
                                  {editingPick === pick.id ? (
                                    <div className="flex items-center space-x-2">
                                      <Select 
                                        value={pick.team} 
                                        onValueChange={(team) => updatePick(pick.id, team, pick.is_underdog)}
                                      >
                                        <SelectTrigger className="w-32">
                                          <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                          {teams.filter(team => 
                                            team === pick.team || 
                                            !currentPicks.some(p => p.id !== pick.id && p.team === team)
                                          ).map((team) => (
                                            <SelectItem key={team} value={team}>{team}</SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                      <Button size="sm" variant="outline" onClick={() => setEditingPick(null)}>
                                        Cancel
                                      </Button>
                                    </div>
                                  ) : (
                                    <div className="flex space-x-2">
                                      <Button size="sm" variant="outline" onClick={() => setEditingPick(pick.id)}>
                                        Edit
                                      </Button>
                                      <Button size="sm" variant="destructive" onClick={() => deletePick(pick.id)}>
                                        Delete
                                      </Button>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                        {gameSettings?.picks_locked && (
                          <p className="text-sm text-gray-600 mt-2">Picks are locked and cannot be edited.</p>
                        )}
                      </div>
                    </div>
                  )}

                  {selectedPlayer && myPlayers.find(p => p.id === selectedPlayer)?.status === 'redemption' ? (
                    <div className="space-y-4">
                      <Alert className="border-yellow-200 bg-yellow-50">
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                        <AlertDescription className="text-yellow-800">
                          <strong>Redemption Round:</strong> You must select 2 different underdog teams to continue.
                        </AlertDescription>
                      </Alert>
                      
                      <div className="space-y-2">
                        <Label>First Underdog Team</Label>
                        <Select value={redemptionPicks.underdogTeam1} onValueChange={(value) => setRedemptionPicks(prev => ({ ...prev, underdogTeam1: value }))}>
                          <SelectTrigger>
                            <SelectValue placeholder="Choose first underdog team" />
                          </SelectTrigger>
                          <SelectContent>
                            {getAvailableTeams(selectedPlayer).map((team) => (
                              <SelectItem key={team} value={team}>{team}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Second Underdog Team</Label>
                        <Select value={redemptionPicks.underdogTeam2} onValueChange={(value) => setRedemptionPicks(prev => ({ ...prev, underdogTeam2: value }))}>
                          <SelectTrigger>
                            <SelectValue placeholder="Choose second underdog team" />
                          </SelectTrigger>
                          <SelectContent>
                            {underdogTeams.filter(team => team !== redemptionPicks.underdogTeam1).map((team) => (
                              <SelectItem key={team} value={team}>{team}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>


                      <Button 
                        onClick={makeRedemptionPicks} 
                        disabled={loading || !redemptionPicks.underdogTeam1 || !redemptionPicks.underdogTeam2 || gameSettings?.picks_locked}
                        className="w-full"
                      >
                        {loading ? 'Submitting...' : 'Submit Redemption Picks'}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Select Team</Label>
                        <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                          <SelectTrigger>
                            <SelectValue placeholder="Choose a team" />
                          </SelectTrigger>
                          <SelectContent>
                            {teams.map((team) => (
                              <SelectItem key={team} value={team}>
                                {team}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <Button 
                        onClick={makePick} 
                        disabled={loading || !selectedPlayer || !selectedTeam || gameSettings?.picks_locked}
                        className="w-full"
                      >
                        {loading ? 'Submitting...' : 'Submit Pick'}
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="leaderboard" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Leaderboard</CardTitle>
                <CardDescription>Current standings and elimination status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {leaderboard.map((entry, index) => (
                    <div key={entry.player_id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="font-bold text-lg w-8">#{index + 1}</span>
                        <div>
                          <div className="font-medium">{entry.entry_name}</div>
                          <div className="text-sm text-gray-600">@{entry.username}</div>
                        </div>
                        {getStatusBadge(entry.status)}
                      </div>
                      <div className="text-right text-sm">
                        <div>Weeks: {entry.weeks_survived}</div>
                        <div className="text-gray-600">
                          R: {entry.redemption_visits} | B: {entry.buybacks}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pot-tracker" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Total Pot</CardTitle>
                  <CardDescription>Combined contributions from all players</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="p-6 bg-green-50 rounded-lg border border-green-200">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-800">
                        ${leaderboard.reduce((total, entry) => total + (entry.financial_contribution || 0), 0).toFixed(2)}
                      </div>
                      <div className="text-lg text-green-600 mt-2">Total Pot</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Individual Contributions</CardTitle>
                  <CardDescription>Breakdown by player</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {leaderboard.length > 0 ? leaderboard
                      .sort((a, b) => (b.financial_contribution || 0) - (a.financial_contribution || 0))
                      .map((entry) => (
                        <div key={entry.player_id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <span className="font-medium">{entry.entry_name}</span>
                            <div className="text-sm text-gray-600">@{entry.username}</div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <span className="text-lg font-semibold text-gray-800 min-w-[80px] text-right">
                              ${(entry.financial_contribution || 0).toFixed(2)}
                            </span>
                            <div className="flex space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleBuyback(entry.player_id)}
                                disabled={loading}
                              >
                                Buyback
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleUndo(entry.player_id)}
                                disabled={loading}
                              >
                                Undo
                              </Button>
                            </div>
                          </div>
                        </div>
                      )) : (
                      <div className="text-center py-8">
                        <div className="text-gray-500 text-lg">No players yet</div>
                        <div className="text-sm text-gray-400 mt-2">Players will appear here once they join the league</div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {user.role === 'admin' && (
            <TabsContent value="admin" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Settings className="h-5 w-5" />
                    <span>Admin Controls</span>
                  </CardTitle>
                  <CardDescription>Manage the survivor league</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">

                    {/* Game Results */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Record Game Results (Week {gameSettings?.current_week})</h3>
                      <div className="border rounded-lg">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Team</TableHead>
                              <TableHead>Result</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {teams.map((team) => (
                              <TableRow key={team}>
                                <TableCell className="font-medium">{team}</TableCell>
                                <TableCell>
                                  <div className="flex space-x-2">
                                    <Button
                                      size="sm"
                                      variant={teamResults[team] === 'win' ? 'default' : 'outline'}
                                      onClick={() => setTeamResults(prev => ({ ...prev, [team]: 'win' }))}
                                    >
                                      Win
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant={teamResults[team] === 'loss' ? 'destructive' : 'outline'}
                                      onClick={() => setTeamResults(prev => ({ ...prev, [team]: 'loss' }))}
                                    >
                                      Loss
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant={teamResults[team] === 'bye' ? 'secondary' : 'outline'}
                                      onClick={() => setTeamResults(prev => ({ ...prev, [team]: 'bye' }))}
                                    >
                                      Bye
                                    </Button>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <Button onClick={recordTableGameResults} disabled={loading}>
                        Record Selected Results
                      </Button>
                    </div>

                    {/* Current Week Results */}
                    {gameResults.length > 0 && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Week {gameSettings?.current_week} Results</h3>
                        <div className="space-y-2">
                          {gameResults.map((result) => (
                            <div key={result.id} className="flex items-center justify-between p-3 border rounded-lg">
                              <span className="font-medium">{result.team}: {result.outcome.toUpperCase()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Week Management */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Week Management</h3>
                      <div className="p-4 border rounded-lg bg-blue-50">
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium text-blue-800">Current Week: {gameSettings?.current_week}</h4>
                              <p className="text-sm text-blue-700">
                                Picks are currently {gameSettings?.picks_locked ? 'locked' : 'open'}
                              </p>
                            </div>
                          </div>
                          <div className="flex space-x-4">
                            <Button 
                              onClick={lockPicksAndAdvanceWeek} 
                              disabled={loading}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              {loading ? 'Processing...' : 'Lock Picks and Advance Week'}
                            </Button>
                            <Button 
                              onClick={unlockPicksAndReturnToPreviousWeek} 
                              disabled={loading || (gameSettings?.current_week || 1) <= 1}
                              variant="outline"
                              className="border-orange-300 text-orange-700 hover:bg-orange-50"
                            >
                              {loading ? 'Processing...' : 'Unlock Picks and Return to Previous Week'}
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Underdog Teams */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Manage Underdog Teams (Week {gameSettings?.current_week})</h3>
                      <div className="border rounded-lg">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Team</TableHead>
                              <TableHead>Underdog Status</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {teams.map((team) => (
                              <TableRow key={team}>
                                <TableCell className="font-medium">{team}</TableCell>
                                <TableCell>
                                  <div className="flex items-center space-x-2">
                                    <input
                                      type="checkbox"
                                      id={`underdog-${team}`}
                                      checked={underdogTeamSelections[team] || underdogTeams.includes(team)}
                                      onChange={(e) => setUnderdogTeamSelections(prev => ({ ...prev, [team]: e.target.checked }))}
                                      className="rounded border-gray-300"
                                    />
                                    <Label htmlFor={`underdog-${team}`}>Underdog</Label>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <Button onClick={saveUnderdogTeams} disabled={loading}>
                        Save Underdog Teams
                      </Button>
                      
                      {underdogTeams.length > 0 && (
                        <div className="space-y-2">
                          <Label>Current Underdog Teams (Week {gameSettings?.current_week})</Label>
                          <div className="flex flex-wrap gap-2">
                            {underdogTeams.map((team) => (
                              <Badge key={team} variant="secondary">{team}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Reset League */}
                    <div className="space-y-4 pt-6 border-t border-red-200">
                      <h3 className="text-lg font-semibold text-red-600">Danger Zone</h3>
                      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                        <div className="space-y-2">
                          <h4 className="font-medium text-red-800">Reset Entire League</h4>
                          <p className="text-sm text-red-700">
                            This will permanently delete all players, picks, game results, underdog teams, and non-admin users. 
                            The league will be reset to Week 1 with default settings.
                          </p>
                          <Button 
                            variant="destructive" 
                            onClick={resetLeague} 
                            disabled={loading}
                            className="mt-2"
                          >
                            {loading ? 'Resetting...' : 'Reset League'}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>

        {error && (
          <Alert className="mt-4 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mt-4 border-green-200 bg-green-50">
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}
      </main>
    </div>
  )
}

export default App
