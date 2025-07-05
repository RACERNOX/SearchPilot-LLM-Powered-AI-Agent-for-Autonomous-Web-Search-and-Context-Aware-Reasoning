# 🚂 Railway Deployment Guide

## Step-by-Step Deployment Instructions

### 1. Sign Up for Railway
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Sign up with your GitHub account

### 2. Get OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up/login to OpenAI
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### 3. Deploy to Railway
1. In Railway dashboard, click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your SearchPilot repository
4. Click "Deploy"

### 4. Configure Environment Variables
1. In your Railway project dashboard
2. Go to "Variables" tab
3. Add new variable:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (sk-...)
4. Save the variable

### 5. Wait for Deployment
- Railway will automatically:
  - Install Python dependencies
  - Build your app
  - Deploy it to a public URL

### 6. Access Your App
- Once deployed, Railway will provide a URL like:
  - `https://your-app-name.up.railway.app`
- Click the URL to access your live SearchPilot!

## 💰 Cost Information
- **Railway Free Tier**: $5 credit monthly (usually enough for moderate usage)
- **OpenAI API**: Pay-per-use (GPT-3.5-turbo is very affordable)
- **Total**: Essentially free for personal/small projects

## 🔧 Troubleshooting

### Common Issues:
1. **Build fails**: Check the logs in Railway dashboard
2. **OpenAI errors**: Ensure API key is set correctly
3. **App won't start**: Check if PORT environment variable is recognized

### Environment Variables Needed:
- `OPENAI_API_KEY` - Your OpenAI API key
- `PORT` - Automatically set by Railway

## 🚀 Going Live Checklist
- [ ] OpenAI API key configured
- [ ] Railway deployment successful
- [ ] App accessible via Railway URL
- [ ] Search functionality working
- [ ] Chat interface responsive

## 📊 Monitoring
- Check Railway dashboard for:
  - Resource usage
  - Logs and errors
  - Performance metrics
  - Deployment status

Your SearchPilot is now live and accessible to users worldwide! 🌍
