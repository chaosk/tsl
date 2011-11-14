import numpy as np
import PIL.Image

"""
http://stackoverflow.com/questions/3374878/#3375291
"""

def alpha_composite(front,back):
	front=np.asarray(front)
	back=np.asarray(back)    
	result=np.empty(front.shape,dtype='float')
	alpha=np.index_exp[:,:,3:]
	rgb=np.index_exp[:,:,:3]
	falpha=front[alpha]/255.0
	balpha=back[alpha]/255.0
	result[alpha]=falpha+balpha*(1-falpha)
	# result[rgb]=(front[rgb]*falpha + back[rgb]*balpha*(1-falpha))/result[alpha]
	result[rgb]=(front[rgb]*falpha + back[rgb]*balpha*(1-falpha))
	result[alpha]*=255
	front_transparent=(falpha<=0.001)&(balpha>0.001)
	result[front_transparent]=back[front_transparent]
	back_transparent=(balpha<=0.001)&(falpha>0.001)
	result[back_transparent]=front[back_transparent]
	result[result>255]=255
	result=result.astype('uint8')
	result=PIL.Image.fromarray(result,'RGBA')
	return result