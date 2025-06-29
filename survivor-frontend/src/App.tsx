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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Trophy, Users, Calendar, Settings, LogOut, Plus, AlertCircle } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'player'
  profile_picture_url?: string
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

interface PickEntry {
  pick_id: string
  week: number
  team: string
  player_name: string
  username: string
  is_redemption: boolean
  is_underdog: boolean
  created_at: string
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
  const [everyonesPicks, setEveryonesPicks] = useState<PickEntry[]>([])
  const [teams, setTeams] = useState<string[]>([])
  const [gameSettings, setGameSettings] = useState<GameSettings | null>(null)
  const [underdogTeams, setUnderdogTeams] = useState<string[]>([])
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)

  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '', profilePicture: null as File | null })
  const [resetPasswordForm, setResetPasswordForm] = useState({ username: '', email: '', newPassword: '' })
  const [profilePicturePreview, setProfilePicturePreview] = useState<string | null>(null)
  const [showResetPassword, setShowResetPassword] = useState(false)
  const [newPlayerName, setNewPlayerName] = useState('')
  const [selectedTeam, setSelectedTeam] = useState('')
  const [allUsers, setAllUsers] = useState<any[]>([])
  const [editableTeams, setEditableTeams] = useState<string[]>([])
  const [newTeamName, setNewTeamName] = useState('')
  const [gameSettingsForm, setGameSettingsForm] = useState({ entry_fee: 35, buyback_multiplier: 3 })
  const [selectedPlayer, setSelectedPlayer] = useState('')
  const [profileForm, setProfileForm] = useState({ username: '', email: '' })
  const [passwordForm, setPasswordForm] = useState({ currentPassword: '', newPassword: '', confirmPassword: '' })
  const [profilePhotoFile, setProfilePhotoFile] = useState<File | null>(null)
  const [profilePhotoPreview, setProfilePhotoPreview] = useState<string | null>(null)
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
      fetchEveryonesPicks()
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
    if (user?.role === 'admin') {
      fetchAllUsers()
      setEditableTeams([...teams])
      setGameSettingsForm({
        entry_fee: gameSettings?.entry_fee || 35,
        buyback_multiplier: gameSettings?.buyback_multiplier || 3
      })
    }
  }, [user, teams, gameSettings])

  useEffect(() => {
    if (user) {
      setProfileForm({ username: user.username, email: user.email })
    }
  }, [user])

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

  const fetchEveryonesPicks = async () => {
    try {
      const picksData = await apiCall('/picks/locked')
      setEveryonesPicks(picksData)
    } catch (err) {
      console.error('Failed to fetch everyone\'s picks:', err)
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

    if (!registerForm.profilePicture) {
      setError('Profile picture is required')
      setLoading(false)
      return
    }

    try {
      const formData = new FormData()
      formData.append('username', registerForm.username)
      formData.append('email', registerForm.email)
      formData.append('password', registerForm.password)
      formData.append('profile_picture', registerForm.profilePicture)

      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Registration failed')
      }

      const data = await response.json()
      setToken(data.token)
      setUser(data.user)
      localStorage.setItem('token', data.token)
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
    setEveryonesPicks([])
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
      fetchEveryonesPicks()
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
      fetchEveryonesPicks()
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
      setEveryonesPicks([])
      setGameResults([])
      setUnderdogTeams([])
      setTeamResults({})
      setCurrentPicks([])
      setSelectedPlayer('')

      fetchGameSettings()
      fetchLeaderboard()
      fetchEveryonesPicks()
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
      await fetchEveryonesPicks()
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
      await fetchLeaderboard()
      await fetchEveryonesPicks()
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
      fetchEveryonesPicks()
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
      fetchEveryonesPicks()
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
      fetchEveryonesPicks()
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

  const fetchAllUsers = async () => {
    try {
      const users = await apiCall('/admin/users')
      setAllUsers(users)
    } catch (err) {
      setError('Failed to fetch users')
    }
  }

  const updateUserRole = async (userId: string, role: string) => {
    try {
      await apiCall('/admin/users/role', {
        method: 'PUT',
        body: JSON.stringify({ user_id: userId, role })
      })
      setSuccess('User role updated successfully')
      fetchAllUsers()
    } catch (err) {
      setError('Failed to update user role')
    }
  }

  const updateGameSettings = async () => {
    try {
      await apiCall('/admin/settings', {
        method: 'PUT',
        body: JSON.stringify(gameSettingsForm)
      })
      setSuccess('Game settings updated successfully')
      fetchGameSettings()
    } catch (err) {
      setError('Failed to update game settings')
    }
  }

  const updateTeams = async () => {
    try {
      await apiCall('/admin/teams', {
        method: 'PUT',
        body: JSON.stringify({ teams: editableTeams })
      })
      setSuccess('Teams updated successfully')
      fetchTeams()
    } catch (err) {
      setError('Failed to update teams')
    }
  }

  const addNewTeam = () => {
    if (newTeamName.trim() && !editableTeams.includes(newTeamName.trim())) {
      setEditableTeams([...editableTeams, newTeamName.trim()])
      setNewTeamName('')
    }
  }

  const removeTeam = (teamToRemove: string) => {
    setEditableTeams(editableTeams.filter(team => team !== teamToRemove))
  }

  const updateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profileForm.username.trim() && !profileForm.email.trim()) {
      setError('Please provide at least one field to update')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const updateData: any = {}
      if (profileForm.username.trim()) updateData.username = profileForm.username.trim()
      if (profileForm.email.trim()) updateData.email = profileForm.email.trim()

      const response = await apiCall('/me', {
        method: 'PUT',
        body: JSON.stringify(updateData)
      })
      setUser(response.user)
      setSuccess('Profile updated successfully!')
      setProfileForm({ username: response.user.username, email: response.user.email })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Profile update failed')
    } finally {
      setLoading(false)
    }
  }

  const updatePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      setError('Please fill in all password fields')
      return
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setError('New passwords do not match')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      await apiCall('/me/password', {
        method: 'PUT',
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword
        })
      })
      setSuccess('Password updated successfully!')
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Password update failed')
    } finally {
      setLoading(false)
    }
  }

  const handleProfilePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setProfilePhotoFile(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        setProfilePhotoPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const updateProfilePhoto = async () => {
    if (!profilePhotoFile) {
      setError('Please select a photo to upload')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const formData = new FormData()
      formData.append('profile_picture', profilePhotoFile)

      const response = await fetch(`${API_URL}/me/profile-picture`, {
        method: 'PUT',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Photo upload failed')
      }

      const data = await response.json()
      setUser({ ...user!, profile_picture_url: data.profile_picture_url })
      setSuccess('Profile photo updated successfully!')
      setProfilePhotoFile(null)
      setProfilePhotoPreview(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Photo upload failed')
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
                  <div className="space-y-2">
                    <Label htmlFor="profile-picture">Profile Picture *</Label>
                    <Input
                      id="profile-picture"
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0] || null
                        setRegisterForm({ ...registerForm, profilePicture: file })
                        if (file) {
                          const reader = new FileReader()
                          reader.onload = (e) => setProfilePicturePreview(e.target?.result as string)
                          reader.readAsDataURL(file)
                        } else {
                          setProfilePicturePreview(null)
                        }
                      }}
                      required
                    />
                    {profilePicturePreview && (
                      <div className="mt-2">
                        <img
                          src={profilePicturePreview}
                          alt="Profile preview"
                          className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                        />
                      </div>
                    )}
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
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="picks">Make Picks</TabsTrigger>
            <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
            <TabsTrigger value="everyone-picks">Everyone's Picks</TabsTrigger>
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

          <TabsContent value="profile" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Update Profile</CardTitle>
                  <CardDescription>Change your username and email address</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={updateProfile} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="profile-username">Username</Label>
                      <Input
                        id="profile-username"
                        type="text"
                        value={profileForm.username}
                        onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                        placeholder="Enter new username"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="profile-email">Email</Label>
                      <Input
                        id="profile-email"
                        type="email"
                        value={profileForm.email}
                        onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                        placeholder="Enter new email"
                      />
                    </div>
                    <Button type="submit" disabled={loading}>
                      {loading ? 'Updating...' : 'Update Profile'}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Change Password</CardTitle>
                  <CardDescription>Update your account password</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={updatePassword} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="current-password">Current Password</Label>
                      <Input
                        id="current-password"
                        type="password"
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="new-password">New Password</Label>
                      <Input
                        id="new-password"
                        type="password"
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password">Confirm New Password</Label>
                      <Input
                        id="confirm-password"
                        type="password"
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                        required
                      />
                    </div>
                    <Button type="submit" disabled={loading}>
                      {loading ? 'Updating...' : 'Update Password'}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Profile Picture</CardTitle>
                <CardDescription>Update your profile photo</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-6">
                    <div className="flex-shrink-0">
                      <Avatar className="h-20 w-20">
                        <AvatarImage 
                          src={user?.profile_picture_url ? `${API_URL}${user.profile_picture_url}` : undefined} 
                          alt={user?.username} 
                        />
                        <AvatarFallback className="text-lg">
                          {user?.username?.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    </div>
                    <div className="flex-1">
                      <div className="space-y-2">
                        <Label htmlFor="profile-photo">Choose new photo</Label>
                        <Input
                          id="profile-photo"
                          type="file"
                          accept="image/jpeg,image/png,image/gif,image/webp"
                          onChange={handleProfilePhotoChange}
                          className="cursor-pointer"
                        />
                        <p className="text-sm text-gray-500">
                          Supported formats: JPEG, PNG, GIF, WebP (max 5MB)
                        </p>
                      </div>
                    </div>
                  </div>

                  {profilePhotoPreview && (
                    <div className="space-y-2">
                      <Label>Preview</Label>
                      <div className="flex items-center space-x-4">
                        <Avatar className="h-16 w-16">
                          <AvatarImage src={profilePhotoPreview} alt="Preview" />
                        </Avatar>
                        <div className="flex space-x-2">
                          <Button onClick={updateProfilePhoto} disabled={loading}>
                            {loading ? 'Uploading...' : 'Upload Photo'}
                          </Button>
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setProfilePhotoFile(null)
                              setProfilePhotoPreview(null)
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {error && (
              <Alert className="border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-200 bg-green-50">
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}
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

          <TabsContent value="everyone-picks" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Everyone's Picks</CardTitle>
                <CardDescription>All locked picks from past weeks and current week (if locked)</CardDescription>
              </CardHeader>
              <CardContent>
                {everyonesPicks.length > 0 ? (
                  <div className="border rounded-lg">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Week</TableHead>
                          <TableHead>Player</TableHead>
                          <TableHead>Username</TableHead>
                          <TableHead>Team</TableHead>
                          <TableHead>Type</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {everyonesPicks.map((pick) => (
                          <TableRow key={pick.pick_id}>
                            <TableCell className="font-medium">{pick.week}</TableCell>
                            <TableCell>{pick.player_name}</TableCell>
                            <TableCell className="text-gray-600">@{pick.username}</TableCell>
                            <TableCell className="font-medium">{pick.team}</TableCell>
                            <TableCell>
                              {pick.is_redemption ? (
                                <Badge variant="destructive">Redemption</Badge>
                              ) : pick.is_underdog ? (
                                <Badge variant="secondary">Underdog</Badge>
                              ) : (
                                <Badge variant="default">Regular</Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-500 text-lg">No locked picks yet</div>
                    <div className="text-sm text-gray-400 mt-2">Picks will appear here once they are locked</div>
                  </div>
                )}
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
                    {/* Game Settings */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Game Settings</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="entry_fee">Entry Fee ($)</Label>
                          <Input
                            id="entry_fee"
                            type="number"
                            value={gameSettingsForm.entry_fee}
                            onChange={(e) => setGameSettingsForm(prev => ({ ...prev, entry_fee: parseInt(e.target.value) || 0 }))}
                          />
                        </div>
                        <div>
                          <Label htmlFor="buyback_multiplier">Buyback Multiplier</Label>
                          <Input
                            id="buyback_multiplier"
                            type="number"
                            value={gameSettingsForm.buyback_multiplier}
                            onChange={(e) => setGameSettingsForm(prev => ({ ...prev, buyback_multiplier: parseInt(e.target.value) || 0 }))}
                          />
                        </div>
                      </div>
                      <Button onClick={updateGameSettings} disabled={loading}>
                        Update Game Settings
                      </Button>
                    </div>

                    {/* User Role Management */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">User Management</h3>
                      <div className="border rounded-lg">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Username</TableHead>
                              <TableHead>Email</TableHead>
                              <TableHead>Current Role</TableHead>
                              <TableHead>Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {allUsers.map((user) => (
                              <TableRow key={user.id}>
                                <TableCell className="font-medium">{user.username}</TableCell>
                                <TableCell>{user.email}</TableCell>
                                <TableCell>
                                  <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                                    {user.role}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <div className="flex space-x-2">
                                    {user.role === 'player' && (
                                      <Button
                                        size="sm"
                                        onClick={() => updateUserRole(user.id, 'admin')}
                                        disabled={loading}
                                      >
                                        Make Admin
                                      </Button>
                                    )}
                                    {user.role === 'admin' && (
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => updateUserRole(user.id, 'player')}
                                        disabled={loading}
                                      >
                                        Remove Admin
                                      </Button>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>

                    {/* Team Management */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Team Management</h3>
                      <div className="space-y-2">
                        <div className="flex space-x-2">
                          <Input
                            placeholder="Add new team (e.g., LAR)"
                            value={newTeamName}
                            onChange={(e) => setNewTeamName(e.target.value)}
                          />
                          <Button onClick={addNewTeam} disabled={loading}>
                            Add Team
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto border rounded p-2">
                          {editableTeams.map((team) => (
                            <div key={team} className="flex items-center space-x-1 bg-gray-100 rounded px-2 py-1">
                              <span className="text-sm">{team}</span>
                              <button
                                onClick={() => removeTeam(team)}
                                className="text-red-500 hover:text-red-700 text-xs"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                        </div>
                        <Button onClick={updateTeams} disabled={loading}>
                          Save Team Changes
                        </Button>
                      </div>
                    </div>

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
