import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Loader2, Lock, Mail } from 'lucide-react'
import { login, connectWhatsapp } from '../lib/api'
import { AuthShell, GoogleAuthButton } from '../components/AuthShell'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function handleChange(event) {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setError('')
  }

  async function handleLogin(event) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await login({
        email: form.email,
        password: form.password,
      })

      const { user, token } = response.data

      localStorage.setItem('auth_token', token)
      localStorage.setItem('aaje_user', JSON.stringify(user))
      localStorage.setItem('aaje_user_id', user.id)

      const params = new URLSearchParams(location.search)
      const wa = params.get('wa')
      if (wa) {
        localStorage.setItem('wa_redirect', 'true')
        try {
          await connectWhatsapp({ whatsapp_no: wa })
        } catch (err) {
          console.error('Failed to link WhatsApp during login', err)
        }
      }

      if (!user.onboarding_complete) {
        navigate('/onboarding')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      console.error('Login error:', err)
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to manage your storefront and WhatsApp operations."
      footer={
        <>
          Don't have an account?{' '}
          <Link to={`/signup${location.search}`} className="font-bold text-[#2f22d8] hover:underline">
            Sign up
          </Link>
        </>
      }
    >
      {error && (
        <div className="mb-5 rounded-[8px] border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-5">
        <Field
          label="Email"
          icon={Mail}
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          placeholder="Enter your email"
          required
        />
        <Field
          label="Password"
          icon={Lock}
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          placeholder="Enter password"
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-12 w-full items-center justify-center rounded-[8px] bg-[#5a4be7] text-sm font-bold text-white transition hover:bg-[#493bd0] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Logging in...
            </>
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      <div className="my-7 flex items-center gap-4">
        <span className="h-px flex-1 bg-[#ece8f3]" />
        <span className="text-xs text-[#a09bac]">or continue with</span>
        <span className="h-px flex-1 bg-[#ece8f3]" />
      </div>

      <GoogleAuthButton label="Google" />
    </AuthShell>
  )
}

function Field({ label, name, value, onChange, icon: Icon, type = 'text', ...props }) {
  return (
    <div>
      <label htmlFor={name} className="mb-2 block text-xs font-bold text-[#17142f]">
        {label}
        {props.required && <span className="text-[#5a4be7]">*</span>}
      </label>
      <div className="flex h-12 items-center gap-3 rounded-[8px] bg-[#fafafa] px-4">
        {Icon && <Icon className="h-4 w-4 text-[#9b97aa]" />}
        <input
          id={name}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          className="min-w-0 flex-1 bg-transparent text-sm text-[#17142f] outline-none placeholder:text-[#9b97aa]"
          {...props}
        />
      </div>
    </div>
  )
}
