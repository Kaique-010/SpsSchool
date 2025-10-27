from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

from courses.models import Module, Training, Video, UserProgress, UserCertificate
from .models import FAQ, SystemSettings, Notification
from users.models import UserProfile


def home(request):
    """Home page view"""
    context = {
        'total_modules': Module.objects.count(),
        'total_trainings': Training.objects.count(),
        'total_videos': Video.objects.count(),
    }
    
    if request.user.is_authenticated:
        # Get user progress statistics
        user_progress = UserProgress.objects.filter(user=request.user)
        
        # Calculate average progress manually since progress_percentage is a property
        total_progress = 0
        progress_count = 0
        for progress in user_progress.select_related('video'):
            if progress.video.duration_seconds > 0:
                percentage = min((progress.progress_seconds / progress.video.duration_seconds) * 100, 100)
                total_progress += percentage
                progress_count += 1
        
        avg_progress = (total_progress / progress_count) if progress_count > 0 else 0
        
        context.update({
            'user_completed_trainings': user_progress.filter(completed=True).count(),
            'user_certificates': UserCertificate.objects.filter(user=request.user).count(),
            'user_total_progress': avg_progress,
        })
        
        # Get recent modules with progress
        recent_modules = Module.objects.prefetch_related('trainings__videos').all()[:6]
        modules_with_progress = []
        
        for module in recent_modules:
            total_videos = sum(training.videos.count() for training in module.trainings.all())
            completed_videos = UserProgress.objects.filter(
                user=request.user,
                video__training__module=module,
                completed=True
            ).count()
            
            progress = (completed_videos / total_videos * 100) if total_videos > 0 else 0
            
            modules_with_progress.append({
                'module': module,
                'progress': round(progress, 1),
                'total_videos': total_videos,
                'completed_videos': completed_videos
            })
        
        context['recent_modules'] = modules_with_progress
    
    # Get FAQ preview
    context['faq_preview'] = FAQ.objects.filter(is_active=True)[:3]
    
    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    """User dashboard view"""
    user = request.user
    
    # Get user statistics
    user_progress = UserProgress.objects.filter(user=user)
    completed_trainings = user_progress.filter(completed=True).count()
    certificates = UserCertificate.objects.filter(user=user).count()
    
    # Calculate overall progress
    total_videos = Video.objects.count()
    completed_videos = user_progress.filter(completed=True).count()
    overall_progress = (completed_videos / total_videos * 100) if total_videos > 0 else 0
    
    # Get recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_progress = user_progress.filter(
        last_watched__gte=week_ago
    ).select_related('video', 'video__training', 'video__training__module').order_by('-last_watched')[:5]
    
    # Get progress by module
    modules_progress = []
    for module in Module.objects.prefetch_related('trainings__videos').all():
        total_videos = sum(training.videos.count() for training in module.trainings.all())
        completed_videos = user_progress.filter(
            video__training__module=module,
            completed=True
        ).count()
        
        progress = (completed_videos / total_videos * 100) if total_videos > 0 else 0
        
        modules_progress.append({
            'module': module,
            'progress': round(progress, 1),
            'total_videos': total_videos,
            'completed_videos': completed_videos
        })
    
    # Get recent certificates
    recent_certificates = UserCertificate.objects.filter(
        user=user
    ).select_related('training').order_by('-issued_at')[:3]
    
    context = {
        'total_modules': Module.objects.count(),
        'completed_trainings': completed_trainings,
        'certificates': certificates,
        'overall_progress': round(overall_progress, 1),
        'recent_activity': recent_progress,
        'modules_progress': modules_progress,
        'recent_certificates': recent_certificates,
    }
    
    return render(request, 'core/dashboard.html', context)


def modules_list(request):
    """List all modules with filtering and search"""
    modules = Module.objects.prefetch_related('trainings__videos').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        modules = modules.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(trainings__title__icontains=search_query)
        ).distinct()
    
    # Filter by status (for authenticated users)
    status_filter = request.GET.get('status', '')
    if request.user.is_authenticated and status_filter:
        user_progress = UserProgress.objects.filter(user=request.user)
        
        if status_filter == 'not_started':
            # Modules with no progress
            started_modules = user_progress.values_list('video__training__module', flat=True).distinct()
            modules = modules.exclude(id__in=started_modules)
        elif status_filter == 'in_progress':
            # Modules with some but not complete progress
            modules_with_progress = []
            for module in modules:
                total_videos = sum(training.videos.count() for training in module.trainings.all())
                completed_videos = user_progress.filter(
                    video__training__module=module,
                    completed=True
                ).count()
                
                if 0 < completed_videos < total_videos:
                    modules_with_progress.append(module.id)
            
            modules = modules.filter(id__in=modules_with_progress)
        elif status_filter == 'completed':
            # Modules with 100% progress
            completed_modules = []
            for module in modules:
                total_videos = sum(training.videos.count() for training in module.trainings.all())
                completed_videos = user_progress.filter(
                    video__training__module=module,
                    completed=True
                ).count()
                
                if total_videos > 0 and completed_videos == total_videos:
                    completed_modules.append(module.id)
            
            modules = modules.filter(id__in=completed_modules)
    
    # Sorting
    sort_by = request.GET.get('sort', 'title')
    if sort_by == 'title':
        modules = modules.order_by('title')
    elif sort_by == 'trainings_count':
        modules = modules.annotate(trainings_count=Count('trainings')).order_by('-trainings_count')
    elif sort_by == 'recent':
        modules = modules.order_by('-created_at')
    
    # Add progress information for authenticated users
    modules_with_progress = []
    for module in modules:
        total_videos = sum(training.videos.count() for training in module.trainings.all())
        total_trainings = module.trainings.count()
        
        module_data = {
            'module': module,
            'total_trainings': total_trainings,
            'total_videos': total_videos,
            'estimated_duration': total_videos * 10,  # Estimate 10 minutes per video
        }
        
        if request.user.is_authenticated:
            user_progress = UserProgress.objects.filter(user=request.user)
            completed_videos = user_progress.filter(
                video__training__module=module,
                completed=True
            ).count()
            
            progress = (completed_videos / total_videos * 100) if total_videos > 0 else 0
            module_data.update({
                'progress': round(progress, 1),
                'completed_videos': completed_videos,
            })
        
        modules_with_progress.append(module_data)
    
    # Pagination
    paginator = Paginator(modules_with_progress, 12)  # 12 modules per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'core/modules_list.html', context)


def module_detail(request, module_id):
    """Module detail view"""
    module = get_object_or_404(Module, id=module_id)
    trainings = module.trainings.prefetch_related('videos').all()
    
    # Calculate module statistics
    total_trainings = trainings.count()
    total_videos = sum(training.videos.count() for training in trainings)
    estimated_duration = total_videos * 10  # Estimate 10 minutes per video
    
    context = {
        'module': module,
        'trainings': trainings,
        'total_trainings': total_trainings,
        'total_videos': total_videos,
        'estimated_duration': estimated_duration,
    }
    
    if request.user.is_authenticated:
        # Get user progress for this module
        user_progress = UserProgress.objects.filter(
            user=request.user,
            video__training__module=module
        )
        
        completed_videos = user_progress.filter(completed=True).count()
        progress = (completed_videos / total_videos * 100) if total_videos > 0 else 0
        
        # Get progress for each training
        trainings_with_progress = []
        for training in trainings:
            training_videos = training.videos.count()
            training_completed = user_progress.filter(
                video__training=training,
                completed=True
            ).count()
            
            training_progress = (training_completed / training_videos * 100) if training_videos > 0 else 0
            
            # Get video progress
            videos_with_progress = []
            for video in training.videos.all():
                video_progress = user_progress.filter(video=video).first()
                videos_with_progress.append({
                    'video': video,
                    'progress': video_progress.progress_percentage if video_progress else 0,
                    'completed': video_progress.completed if video_progress else False,
                })
            
            trainings_with_progress.append({
                'training': training,
                'progress': round(training_progress, 1),
                'completed_videos': training_completed,
                'total_videos': training_videos,
                'videos': videos_with_progress,
            })
        
        context.update({
            'progress': round(progress, 1),
            'completed_videos': completed_videos,
            'trainings_with_progress': trainings_with_progress,
        })
    
    return render(request, 'core/module_detail.html', context)


def video_detail(request, video_id):
    """Video detail view"""
    video = get_object_or_404(Video, id=video_id)
    training = video.training
    module = training.module
    
    # Get all videos in this training for navigation
    training_videos = training.videos.order_by('order_index').all()
    current_index = list(training_videos).index(video)
    
    previous_video = training_videos[current_index - 1] if current_index > 0 else None
    next_video = training_videos[current_index + 1] if current_index < len(training_videos) - 1 else None
    
    context = {
        'video': video,
        'training': training,
        'module': module,
        'training_videos': training_videos,
        'previous_video': previous_video,
        'next_video': next_video,
        'current_index': current_index + 1,
        'total_videos': len(training_videos),
    }
    
    if request.user.is_authenticated:
        # Get or create user progress
        user_progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={'progress_seconds': 0}
        )
        
        # Get training progress
        training_progress = UserProgress.objects.filter(
            user=request.user,
            video__training=training
        )
        
        completed_videos = training_progress.filter(completed=True).count()
        total_training_videos = training.videos.count()
        training_progress_percentage = (completed_videos / total_training_videos * 100) if total_training_videos > 0 else 0
        
        # Get videos with progress for sidebar
        videos_with_progress = []
        for v in training_videos:
            v_progress = training_progress.filter(video=v).first()
            videos_with_progress.append({
                'video': v,
                'progress': v_progress.progress_percentage if v_progress else 0,
                'completed': v_progress.completed if v_progress else False,
                'is_current': v.id == video.id,
            })
        
        context.update({
            'user_progress': user_progress,
            'training_progress': round(training_progress_percentage, 1),
            'completed_videos': completed_videos,
            'videos_with_progress': videos_with_progress,
        })
    
    return render(request, 'core/video_detail.html', context)


@login_required
def profile(request):
    """User profile view"""
    user = request.user
    
    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=user)
    
    # Get user statistics
    user_progress = UserProgress.objects.filter(user=user)
    completed_trainings = user_progress.filter(completed=True).count()
    certificates = UserCertificate.objects.filter(user=user).count()
    
    # Calculate total hours (estimate)
    total_hours = user_progress.filter(completed=True).count() * 0.17  # ~10 minutes per video
    
    # Get recent certificates
    recent_certificates = UserCertificate.objects.filter(
        user=user
    ).select_related('training').order_by('-issued_at')[:4]
    
    context = {
        'user_profile': user_profile,
        'completed_trainings': completed_trainings,
        'certificates': certificates,
        'total_hours': round(total_hours, 1),
        'recent_certificates': recent_certificates,
    }
    
    return render(request, 'core/profile.html', context)


def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login realizado com sucesso!')
                
                # Redirect to next page or dashboard
                next_page = request.GET.get('next', 'core:dashboard')
                return redirect(next_page)
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
    
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('core:home')


@login_required
def certificates(request):
    """User certificates view"""
    user_certificates = UserCertificate.objects.filter(
        user=request.user
    ).select_related('training', 'training__module').order_by('-issued_at')
    
    # Filter by category if specified
    category = request.GET.get('category', '')
    if category:
        # This would need to be implemented based on your category system
        pass
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        user_certificates = user_certificates.filter(
            Q(training__title__icontains=search_query) |
            Q(training__module__title__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(user_certificates, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category': category,
    }
    
    return render(request, 'core/certificates.html', context)


def faq(request):
    """FAQ view"""
    faqs = FAQ.objects.filter(is_active=True).order_by('question')
    
    # Group FAQs by category if needed
    faq_categories = {}
    for faq_item in faqs:
        category = faq_item.category or 'general'
        if category not in faq_categories:
            faq_categories[category] = []
        faq_categories[category].append(faq_item)
    
    context = {
        'faqs': faqs,
        'faq_categories': faq_categories,
    }
    
    return render(request, 'core/faq.html', context)
