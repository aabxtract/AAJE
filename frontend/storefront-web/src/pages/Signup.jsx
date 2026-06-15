import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Lock, Loader2, Mail, Phone, User } from 'lucide-react'
import { signup } from '../lib/api'
import { AuthShell, GoogleAuthButton } from '../components/AuthShell'

export default function Signup() {
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const wa = params.get('wa')
    if (wa) {
      setForm(prev => ({ ...prev, phone: wa }))
      localStorage.setItem('wa_redirect', 'true')
    }
    
  }, [location.search])

  function handleChange(event) {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
    setError('')
  }

  async function handleSignup(event) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await signup({
        email: form.email,
        password: form.password,
        full_name: form.fullName,
        phone: form.phone,
      })

      // Backend returns `access_token`; destructuring as `token` would store
      // the literal "undefined" and break every JWT-protected call after this.
      const { user, access_token: token } = response.data

      localStorage.setItem('auth_token', token)
      localStorage.setItem('aaje_user', JSON.stringify(user))
      localStorage.setItem('aaje_user_id', user.id)

      navigate('/onboarding')
    } catch (err) {
      console.error('Signup error:', err)
      setError(err.response?.data?.detail || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start with a free account. No card required."
      footer={
        <>
          Already have an account?{' '}
          <Link to={`/login${location.search}`} className="font-bold text-[#2f22d8] hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      {error && (
        <div className="mb-5 rounded-[8px] border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSignup} className="space-y-5">
        <Field
          label="Name"
          icon={User}
          name="fullName"
          value={form.fullName}
          onChange={handleChange}
          placeholder="Enter your name"
          required
        />
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
          label="Phone"
          icon={Phone}
          name="phone"
          type="tel"
          value={form.phone}
          onChange={handleChange}
          placeholder="Enter your phone number"
          required
        />
        <Field
          label="Password"
          icon={Lock}
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          placeholder="Create password"
          minLength={8}
          hint="Must be at least 8 characters."
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
              Creating account...
            </>
          ) : (
            'Sign Up'
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

function Field({ label, name, value, onChange, icon: Icon, hint, type = 'text', ...props }) {
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
      {hint && <p className="mt-2 text-xs text-[#8a849b]">{hint}</p>}
    </div>
  )
}
